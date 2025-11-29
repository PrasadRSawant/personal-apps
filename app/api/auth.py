from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.orm import Session
from datetime import timedelta

# For Basic Auth
from app.core.dependencies import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.schemas.user import UserCreate
from app.schemas.token import Token
from app.db.models import User

# For Google SSO
from fastapi_sso.sso.google import GoogleSSO
from app.core.config import settings

# Fast API + redis limmiter 
from fastapi_limiter.depends import RateLimiter

router = APIRouter()

# Initialize Google SSO
sso = GoogleSSO(
    settings.GOOGLE_CLIENT_ID, 
    settings.GOOGLE_CLIENT_SECRET, 
    settings.REDIRECT_URI, 
    allow_insecure_http=True # Use False in production with HTTPS
)

# --- Basic Auth Endpoints ---
# Applied Limiter to registration endpoint as Allow only 5 registrations per 10 seconds per IP
@router.post(
    "/basic/register", 
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(RateLimiter(times=5, seconds=10))
    ]
)
def register_user(
    user_data: UserCreate, 
    db: Session = Depends(get_db)
):
    """Creates a new user for Basic Authentication."""
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email, 
        hashed_password=hashed_password, 
        auth_method="Basic"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully."}

@router.post("/basic/token", response_model=Token)
def basic_auth_login_for_access_token(
    form_data: HTTPBasicCredentials = Depends(), 
    db: Session = Depends(get_db)
):
    """Exchanges username/password for a JWT token."""
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Google SSO Endpoints ---

@router.get("/google/login")
async def google_login():
    """Redirects to Google's login page."""
    return await sso.get_login_redirect()

@router.get("/google/callback", response_model=Token)
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handles the callback from Google, authenticates, and returns JWT."""
    try:
        # Verify and process the login via Google
        user_info = await sso.verify_and_process(request)
        user_email = user_info.email
        
        db_user = db.query(User).filter(User.email == user_email).first()
        
        # 1. Register or Retrieve User
        if not db_user:
            new_user = User(
                email=user_email, 
                auth_method="SSO", 
                hashed_password=None
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            db_user = new_user

        # 2. Generate JWT
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.email}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        # Log the error for debugging
        print(f"SSO Error: {e}")
        raise HTTPException(status_code=400, detail="Google SSO failed.")