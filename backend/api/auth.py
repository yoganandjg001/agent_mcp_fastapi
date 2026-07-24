import os
import time
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Load Environment Variables from .env file
load_dotenv()

# JWT Configuration Constants
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "agentic_ai_hackathon_super_secret_key_2026")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRATION_SECONDS = int(os.getenv("TOKEN_EXPIRATION_SECONDS", 3600))

# Security Scheme
security = HTTPBearer()

# Pydantic Authentication Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    full_name: str
    role: str

def create_jwt_token(data: dict) -> str:
    """Generates a signed JWT access token with expiry."""
    payload = data.copy()
    payload["exp"] = int(time.time()) + TOKEN_EXPIRATION_SECONDS
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Validates JWT bearer token and extracts user claims."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token."
        )

def require_approver_role(current_user: dict) -> None:
    """Verifies that the authenticated user possesses the 'approver' role."""
    if current_user.get("role") != "approver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: User '{current_user.get('sub')}' has role '{current_user.get('role')}'. Only users with 'approver' role can perform approvals."
        )
