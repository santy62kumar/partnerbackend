from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud.ip import verify_ip_user, get_ip_by_phone, get_all_ips
from app.core.security import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/verify-ip/{phone_number}")
def verify_ip(phone_number: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_ip = get_ip_by_phone(db, phone_number)
    if not db_ip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IP user not found"
        )
    
    verified_ip = verify_ip_user(db, phone_number)
    return {
        "message": "IP user verified successfully",
        "phone_number": verified_ip.phone_number,
        "is_idverified": verified_ip.is_idverified
    }

@router.get("/ips")
def get_ips(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return get_all_ips(db)