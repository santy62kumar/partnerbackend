from fastapi import APIRouter, Depends, HTTPException, UploadFile, status, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.model.ip import ip
from app.model.job import Job

from app.model.user_document import UserDocument
from app.schemas.ip import (
    PANVerification, 
    BankVerification,
    UserDetailResponse
)
from app.services.pan_service import PANService
from app.services.bank_service import BankService
from app.api.deps import get_verified_user
from app.services.s3_service import upload_file_to_s3

router = APIRouter(prefix="/verification", tags=["Verification"])


@router.post("/pan")
def verify_pan(
    pan_data: PANVerification,
    current_user: ip = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """Verify PAN card details"""
    
    # Check if already verified
    if current_user.is_pan_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PAN already verified for this user"
        )
    
    # Verify PAN using external API
    result = PANService.verify_pan(pan_data.pan)
    
    if not result["verified"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "PAN verification failed")
        )
    
    # Update user record
    current_user.is_pan_verified = True
    current_user.pan_number = result["pan_number"]
    current_user.pan_name = result.get("name")
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "PAN verified successfully",
        "pan_number": result["pan_number"],
        "name": result.get("name")
    }


@router.post("/bank")
def verify_bank(
    bank_data: BankVerification,
    current_user: ip = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """Verify bank account details"""
    
    # Check if already verified
    if current_user.is_bank_details_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bank account already verified for this user"
        )
    
    # Verify bank account using external API
    result = BankService.verify_bank_account(
        bank_data.account_number,
        bank_data.ifsc,
        bank_data.fetch_ifsc
    )
    
    if not result["verified"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Bank account verification failed")
        )
    
    # Update user record
    current_user.is_bank_details_verified = True
    current_user.account_number = result["account_number"]
    current_user.ifsc_code = result["ifsc_code"]
    current_user.account_holder_name = result.get("account_holder_name")
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Bank account verified successfully",
        "account_number": result["account_number"],
        "ifsc_code": result["ifsc_code"],
        "account_holder_name": result.get("account_holder_name"),
        "bank_name": result.get("bank_name"),
        "branch": result.get("branch")
    }


@router.get("/status", response_model=UserDetailResponse)
def get_verification_status(
    current_user: ip = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """Get current verification status of the user"""
    
    return current_user



@router.get("/panel-access")
def check_panel_access(
    current_user: ip = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """Check if user has completed all verifications"""

    all_verified = (
        current_user.is_verified and
        current_user.is_pan_verified and
        current_user.is_bank_details_verified
    )

    
    if all_verified:
        
        jobs = db.query(Job).all()

        job_data = [
            {
                "id": job.id,
                "name": job.name,
                "customer_name": job.customer_name,
                "address": job.address,
                "city": job.city,
                "status": job.status,
                "pincode": job.pincode,
                "assigned_ip_id": job.assigned_ip_id,
                "type": job.type,
                "rate": job.rate,
                "size": job.size,
                "delivery_date": job.delivery_date,
                "checklist_link": job.checklist_link
            }
            for job in jobs
        ]

        return {
            "has_full_access": True,
            "message": "All verifications complete",
            "jobs": job_data
        }

    # ❌ If not verified, return verification status
    return {
        "has_full_access": False,
        "verification_status": {
            "phone_verified": current_user.is_verified,
            "pan_verified": current_user.is_pan_verified,
            "bank_verified": current_user.is_bank_details_verified,
            "id_verified": current_user.is_id_verified
        },
        "message": "Please complete pending verifications"
    }


@router.post("/verify_document")
async def upload_user_document(
    file: UploadFile = File(...),
    current_user: ip = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    # 1️⃣ Upload file to S3
    file_content = await file.read()
    file_url = upload_file_to_s3(
        file_content=file_content,
        filename=file.filename,
        content_type=file.content_type
    )

    # 2️⃣ Create a new UserDocument entry
    new_document = UserDocument(
        status="pending",  # default status for newly uploaded documents
        doc_link=file_url
    )

    # 3️⃣ Add and commit to DB
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    # 4️⃣ Return response
    return {
        "message": "Document uploaded successfully",
        "document_id": new_document.id,
        "doc_link": new_document.doc_link,
        "status": new_document.status,
        "uploaded_at": new_document.uploaded_at
    }
