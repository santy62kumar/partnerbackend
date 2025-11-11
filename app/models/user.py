from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from app.database import Base


class User(Base):
    __tablename__ = "ip_user"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    address = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    
    # Verification flags
    is_verified = Column(Boolean, default=False)
    is_pan_verified = Column(Boolean, default=False)
    is_bank_details_verified = Column(Boolean, default=False)
    is_id_verified = Column(Boolean, default=False)
    otp = Column(String, nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    
    # Verification details
    pan_number = Column(String, nullable=True)
    pan_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)
    account_holder_name = Column(String, nullable=True)
    
    # Timestamps
    registered_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User {self.phone_number}>"