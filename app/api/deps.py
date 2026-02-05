from fastapi import Depends, Request, HTTPException, status, Cookie, Header
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.model.ip import ip
from app.utils.helpers import verify_token

security = HTTPBearer()


# def get_current_user(
#     request: Request,
#     db: Session = Depends(get_db)
# ) -> ip:
#     token = request.cookies.get("auth-token")

#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Not authenticated"
#         )
    
#     payload = verify_token(token)
#     if payload is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token"
#         )
    
#     id = payload.get("sub")
#     if id is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token payload"
#         )
    
#     user = db.query(ip).filter(ip.id == id).first()
#     if user is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     return user


# def get_current_user(
#     # request: Request,
#     # db: Session = Depends(get_db),
#     # # authorization: Optional[str] = Header(None)  # ✅ Add this
#     # authorization: Optional[str] = Header(None, alias="Authorization")

#     request: Request,
#     db: Session = Depends(get_db),
#     credentials: HTTPAuthorizationCredentials = Depends(security)
# ) -> ip:
#     # token = None
#     token = credentials.credentials  # ✅ Get token this way
#     print(f"🔑 Token received: {token[:20]}...")

#     print(f"📨 Received headers: {request.headers}")  # ✅ See all headers
#     print(f"🔐 Authorization header: {authorization}")  # ✅ See what we got
    
#     # ✅ Try to get token from Authorization header first (Bearer token)
#     if authorization and authorization.startswith("Bearer "):
#         token = authorization.replace("Bearer ", "")
#         print("🔑 Token from Authorization header", token)
    
#     # ✅ Fallback to cookie if no Authorization header
#     if not token:
#         token = request.cookies.get("auth-token")
#         if token:
#             print("🍪 Token from cookie")
    
#     # ❌ No token found in either place
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Not authenticated"
#         )
    
#     # Verify token
#     payload = verify_token(token)
#     if payload is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token"
#         )
    
#     id = payload.get("sub")
#     if id is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token payload"
#         )
    
#     # Get user from database
#     user = db.query(ip).filter(ip.id == id).first()
#     if user is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     return user



# security = HTTPBearer()

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)  # ✅ Changed
) -> ip:
    token = credentials.credentials  # ✅ Get token this way
    # print(f"🔑 Token received: {token[:20]}...")
    
    # Verify token
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    id = payload.get("sub")
    if id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database
    user = db.query(ip).filter(ip.id == id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

def get_verified_user(current_user: ip = Depends(get_current_user)) -> ip:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Phone number not verified"
        )
    return current_user
