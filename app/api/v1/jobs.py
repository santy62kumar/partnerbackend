from fastapi import APIRouter, Depends,Form, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.model.ip import ip
from app.model.job import Job
from app.api.deps import get_verified_user
from app.services.s3_service import upload_file_to_s3
from app.model.job_status_log import JobStatusLog
from app.model.job_media import JobMedia
from typing import List

router = APIRouter(prefix="/dashboard/jobs", tags=["Dashboard"])


# ✅ Get all jobs (only if verified)
@router.get("")
def get_all_jobs(
    current_user: ip = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    # jobs = db.query(Job).all()
    jobs = db.query(Job).filter(Job.assigned_ip_id == current_user.id).all()
    print("Jobs fetched:", jobs)
    
    jobs_data = []
    for job in jobs:
        jobs_data.append({
            "id": job.id,
            "name": job.name,
            "customer_name": job.customer_name,
            "address": job.address,
            "city": job.city,
            "status": job.status,
            "pincode": job.pincode,
            "assigned_ip_id": job.assigned_ip_id,
            "type": job.type,
            "rate": float(job.rate),
            "size": job.size,
            "delivery_date": job.delivery_date,
            "checklist_link": job.checklist_link,
            "google_map_link": job.google_map_link,
            "start_date": job.start_date,

            # ⭐ checklist IDs from association table
            "checklist_ids": [c.id for c in job.checklists]
        })

    return {
        "message": "Jobs fetched successfully",
        "total": len(jobs_data),
        "jobs": jobs_data
    } 


# ✅ Get single job by ID
@router.get("/{job_id}")
def get_single_job(
    job_id: int,
    current_user: ip = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    job_data = {
        "id": job.id,
        "name": job.name,
        "customer_name": job.customer_name,
        "address": job.address,
        "city": job.city,
        "status": job.status,
        "pincode": job.pincode,
        "assigned_ip_id": job.assigned_ip_id,
        "type": job.type,
        "rate": float(job.rate),
        "size": job.size,
        "delivery_date": job.delivery_date,
        "checklist_link": job.checklist_link,
        "google_map_link": job.google_map_link,
        "start_date": job.start_date,

        # ⭐ from association table
        # "checklist_ids": [c.id for c in job.checklists]
        "checklists": [
        {
            "id": c.id,
            "name": c.name
        }
        for c in job.checklists
        ]
    }

    return {
        "message": "Job fetched successfully",
        "job": job_data
    }



@router.post("/{job_id}/upload")
async def upload_multiple_files(
    job_id: int,
    file: UploadFile = File(...),
    comment: str = Form(None),
    current_user: ip = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    # 1️⃣ Validate job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 2️⃣ Upload file to S3
    file_content = await file.read()
    file_url = upload_file_to_s3(
        file_content=file_content,
        filename=file.filename,
        content_type=file.content_type
    )

    # 3️⃣ Create a new JobMedia entry
    new_media = JobMedia(
        job_id=job_id,
        status=job.status,       # store the current job status
        doc_link=file_url,
        comment=comment
    )

    # 4️⃣ Add and commit to DB
    db.add(new_media)
    db.commit()
    db.refresh(new_media)

    # 5️⃣ Return response
    return {
        "message": "File uploaded and saved successfully",
        "job_id": job_id,
        "doc_link": new_media.doc_link,
        "comment": new_media.comment
    }

@router.get("/{job_id}/progress")
async def get_job_progress(
    job_id: int,
    current_user: ip = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    # 1️⃣ Validate if job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 2️⃣ Fetch all media entries for this job (ordered by upload time)
    media_records = (
        db.query(JobMedia)
        .filter(JobMedia.job_id == job_id)
        .order_by(JobMedia.uploaded_at.desc())
        .all()
    )

    # 3️⃣ Transform the result for clean JSON response
    result = [
        {
            "id": media.id,
            "job_id": media.job_id,
            "status": media.status,
            "doc_link": media.doc_link,
            "comment": media.comment,
            "uploaded_at": media.uploaded_at,
        }
        for media in media_records
    ]

    # 4️⃣ Return the structured response
    return {
        "job_id": job_id,
        "job_status": job.status,
        "total_uploads": len(result),
        "uploads": result,
    }



