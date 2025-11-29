import base64
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.core.dependencies import get_current_user

router = APIRouter()

# Schema for Base64 input (assuming you add it to app/schemas/file.py)
# class Base64In(BaseModel):
#     base64_string: str
#     filename: str

@router.post("/to-base64", summary="Convert file to Base64")
async def file_to_base64_endpoint(
    file: UploadFile = File(...), 
    current_user: str = Depends(get_current_user) # Protected
):
    """Accepts any file and returns its Base64 encoded string."""
    contents = await file.read()
    encoded_string = base64.b64encode(contents).decode('utf-8')
    
    return {
        "filename": file.filename, 
        "base64_string": encoded_string,
        "user": {
            "email": current_user.email,
            "auth_method": current_user.auth_method,
            "is_active": current_user.is_active,
            "id": current_user.id
        }
    }

@router.post("/from-base64", summary="Convert Base64 string to raw file bytes")
async def base64_to_file_endpoint(
    data: dict, # Using dict for simplicity, use a Pydantic model for production
    current_user: str = Depends(get_current_user) # Protected
):
    """Accepts a Base64 string and returns the decoded bytes (for saving or direct use)."""
    try:
        base64_string = data.get("base64_string")
        if not base64_string:
            raise HTTPException(status_code=400, detail="Missing base64_string")
            
        decoded_bytes = base64.b64decode(base64_string)
        
        return {
            "message": "Base64 decoded successfully", 
            "file_size_bytes": len(decoded_bytes),
            # In a real app, you might return the bytes in a StreamingResponse
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Base64 string: {e}")