from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any, Dict
import logging.config
from pythonjsonlogger import jsonlogger

class Settings(BaseSettings):
    # This setting tells Pydantic where to look for environment variables (the .env file)
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # --- Database Settings (Loaded from .env) ---
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    
    # Final Database URL - calculated dynamically
    SQLALCHEMY_DATABASE_URL: str | None = None

    # --- JWT Security Settings (Can be in .env or hardcoded) ---
    SECRET_KEY: str = "your-strong-jwt-secret-key-change-this" 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- Google SSO Settings (Load from .env if available, or use placeholders) ---
    GOOGLE_CLIENT_ID: str = "YOUR_GOOGLE_CLIENT_ID_FROM_CONSOLE"
    GOOGLE_CLIENT_SECRET: str = "YOUR_GOOGLE_CLIENT_SECRET_FROM_CONSOLE"
    REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # -------------------------------------------------------------
    # Pydantic Model Validator to construct the final URL
    # -------------------------------------------------------------
    @model_validator(mode='before')
    def assemble_db_connection(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # Check if the individual parts are present
        if all(k in values for k in ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB","CORS_ALLOWED_ORIGINS","REDIS_URL"]):
            
            user = values.get("POSTGRES_USER")
            password = values.get("POSTGRES_PASSWORD")
            host = values.get("POSTGRES_HOST")
            port = values.get("POSTGRES_PORT")
            db = values.get("POSTGRES_DB")
            cors_origins = values.get("CORS_ALLOWED_ORIGINS")
            redis_url = values.get("REDIS_URL")

            # Construct the URL, handling the password encoding if necessary (though the DB adapter handles most cases)
            db_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
            
            # Add the constructed URL back into the values dictionary
            values["SQLALCHEMY_DATABASE_URL"] = db_url
            values["CORS_ALLOWED_ORIGINS"] = cors_origins
            values["POSTGRES_USER"] = user
            values["POSTGRES_PASSWORD"] = password
            values["POSTGRES_HOST"] = host
            values["POSTGRES_PORT"] = port
            values["POSTGRES_DB"] = db
            values["REDIS_URL"] = redis_url
        return values

settings = Settings()

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    # FIX: Use *args and **kwargs to accept all arguments passed by the logging system
    def add_fields(self, log_record, message_dict, *args, **kwargs):
        super(CustomJsonFormatter, self).add_fields(log_record, message_dict, *args, **kwargs)
        # Add your service name and environment to every log record
        log_record['service'] = 'fastapi-app'
        log_record['environment'] = 'production' 
        
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": CustomJsonFormatter,
            "format": "%(asctime) %(levelname) %(name) %(module) %(funcName) %(lineno) %(message)"
        },
        "default": {
            "fmt": "%(levelname)s: %(name)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "json_handler": {
            "formatter": "json",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        # Root logger configuration
        "": {
            "handlers": ["json_handler"],
            "level": "INFO",
            "propagate": False,
        },
        # Ensure Uvicorn logs (requests, errors) are also JSON formatted
        "uvicorn.access": {
            "handlers": ["json_handler"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["json_handler"],
            "level": "INFO",
            "propagate": False,
        },
        # Set SQLAlchemy logger to INFO or WARNING to avoid verbose output
        "sqlalchemy.engine": {
            "handlers": ["json_handler"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

def configure_logging():
    logging.config.dictConfig(LOGGING_CONFIG)