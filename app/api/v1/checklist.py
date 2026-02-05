"""
Checklist API Routes
Handles all checklist-related endpoints with optimized queries and batch operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.model.ip import ip
from app.api.deps import get_verified_user
from app.services.s3_service import upload_file_to_s3
from app.model.checklist import Checklist, ChecklistItem, JobChecklistItemStatus

# from app.schemas.checklist_item import ChecklistItemWithStatusResponse

# Import schemas
from app.schemas.checklist import (
    BulkChecklistResponse,
    ChecklistResponse,
    ChecklistItemResponse,
    ChecklistSummaryResponse,
    BatchUpdateRequest,
    BatchUpdateResponse,
    DocumentUploadResponse,
    JobChecklistsSummaryResponse
)

# Import utilities
from app.utils.checklist import (
    verify_job_access,
    verify_checklist_access,
    verify_checklist_items,
    # calculate_checklist_stats,
    # calculate_job_checklists_stats,
    # calculate_checklist_stats,
    get_checklist_with_items,
    get_job_checklists,
    get_job_checklist_statuses,
    get_job_checklist_items_with_status,
    apply_batch_updates
)

router = APIRouter(prefix="/dashboard/jobs", tags=["Checklist"])


# ==================== Main Endpoints ====================

@router.get("/{job_id}/checklist/{checklist_id}", response_model=BulkChecklistResponse)
async def get_checklist_with_all_items(
    job_id: int,
    checklist_id: int,
    current_user: ip = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    
    
    # Verify access
    job = verify_job_access(job_id, current_user, db)
    checklist = verify_checklist_access(checklist_id, job_id, db)
    
    # Fetch items with optimized query
    _, items = get_checklist_with_items(checklist_id, db)
    
   
    result = get_job_checklist_items_with_status(job_id, checklist_id, db)

    
    # Build response
    return BulkChecklistResponse(
        job_id=job.id,
        job_title=getattr(job, 'title', f"Job {job.id}"),
        checklist=ChecklistResponse.from_orm(checklist),
        items=result["items"],
        **result["stats"]
    )


# @router.post("/{job_id}/checklist/{checklist_id}/update", response_model=BatchUpdateResponse)
# async def batch_update_items(
#     job_id: int,
#     checklist_id: int,
#     batch_request: BatchUpdateRequest,
#     current_user: ip = Depends(get_verified_user),
#     db: Session = Depends(get_db)
# ):
    
    
#     # Verify access
#     job = verify_job_access(job_id, current_user, db)
#     checklist = verify_checklist_access(checklist_id, job_id, db)
    
#     # Extract item IDs
#     item_ids = [update.id for update in batch_request.updates]
    
#     # Verify all items exist and belong to checklist
#     _, items_map = verify_checklist_items(item_ids, checklist_id, db)
    
#     # Convert Pydantic models to dicts for processing
#     updates_dict = [update.dict(exclude_none=True) for update in batch_request.updates]
    
#     # Apply batch updates
#     updated_items = apply_batch_updates(items_map, updates_dict, db)
    
#     # Return response
#     return BatchUpdateResponse(
#         success=True,
#         message=f"Successfully updated {len(updated_items)} item(s)",
#         updated_count=len(updated_items),
#         items=[ChecklistItemResponse.from_orm(item) for item in updated_items]
#     )


@router.post("/{job_id}/checklist/{checklist_id}/batch-update", response_model=BatchUpdateResponse)
async def batch_update_items(
    job_id: int,
    checklist_id: int,
    batch_request: BatchUpdateRequest,
    current_user: ip = Depends(get_verified_user),  # Fixed: ip -> User
    db: Session = Depends(get_db)
):
    """
    Batch update checklist item statuses for a specific job
    """
    
    # Verify access
    job = verify_job_access(job_id, current_user, db)
    checklist = verify_checklist_access(checklist_id, job_id, db)
    
    # Extract checklist item IDs
    item_ids = [update.checklist_item_id for update in batch_request.updates]
    
    # Verify all checklist items exist and belong to this checklist
    checklist_items = (
        db.query(ChecklistItem)
        .filter(
            ChecklistItem.id.in_(item_ids),
            ChecklistItem.checklist_id == checklist_id
        )
        .all()
    )
    
    if len(checklist_items) != len(item_ids):
        found_ids = {item.id for item in checklist_items}
        missing_ids = set(item_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist items not found: {missing_ids}"
        )
    
    # Get or create job checklist item statuses
    existing_statuses = (
        db.query(JobChecklistItemStatus)
        .filter(
            JobChecklistItemStatus.job_id == job_id,
            JobChecklistItemStatus.checklist_item_id.in_(item_ids)
        )
        .all()
    )
    
    # Create a map of existing statuses
    status_map = {status.checklist_item_id: status for status in existing_statuses}
    
    # Apply updates
    updated_statuses = []
    
    for update in batch_request.updates:
        # Get or create status record
        if update.checklist_item_id in status_map:
            status_record = status_map[update.checklist_item_id]
        else:
            # Create new status record
            status_record = JobChecklistItemStatus(
                job_id=job_id,
                checklist_item_id=update.checklist_item_id,
                checked=False,
                is_approved=False
            )
            db.add(status_record)
        
        # Update fields (only if provided)
        if update.checked is not None:
            status_record.checked = update.checked
        if update.is_approved is not None:
            status_record.is_approved = update.is_approved
        if update.comment is not None:
            status_record.comment = update.comment
        if update.admin_comment is not None:
            status_record.admin_comment = update.admin_comment
        if update.document_link is not None:
            status_record.document_link = update.document_link
        
        updated_statuses.append(status_record)
    
    # Commit changes
    db.commit()

    result = get_job_checklist_items_with_status(job_id, checklist_id, db)
    stats = result["stats"]
    
    # Refresh all updated records
    for status_record in updated_statuses:
        db.refresh(status_record)
    
    # Build response with items + their status
    items_response = []
    checklist_items_map = {item.id: item for item in checklist_items}
    
    for status_record in updated_statuses:
        item = checklist_items_map[status_record.checklist_item_id]
        items_response.append({  # ✅ Changed to dict
            "id": item.id,
            "text": item.text,
            "position": item.position,
            "created_at": item.created_at,
            "status_id": status_record.id,
            "checked": status_record.checked,
            "is_approved": status_record.is_approved,
            "comment": status_record.comment,
            "admin_comment": status_record.admin_comment,
            "document_link": status_record.document_link
        })

    return BatchUpdateResponse(
        success=True,
        message=f"Successfully updated {len(updated_statuses)} item(s)",
        updated_count=len(updated_statuses),
        items=items_response,
        total_items=stats["total_items"],
        checked_count=stats["checked_count"],
        pending_count=stats["pending_count"],
        approved_count=stats["approved_count"],
        completion_percentage=stats["completion_percentage"]
    )


@router.post(
    "/{job_id}/checklist/{checklist_id}/items/{item_id}/upload",
    response_model=DocumentUploadResponse
)
async def upload_item_document(
    job_id: int,
    checklist_id: int,
    item_id: int,
    file: UploadFile = File(...),
    comment: Optional[str] = Form(None),
    current_user: ip = Depends(get_verified_user),  # Fixed: ip -> User
    db: Session = Depends(get_db)
):
    """
    📤 **DOCUMENT UPLOAD: Upload document for a checklist item**
    
    **What this does:**
    - Uploads file to S3 storage
    - Updates checklist item status with document URL for this specific job
    - Optionally adds/updates comment
    
    **Supported file types:** PDF, Images, Documents
    
    **Use cases:**
    - Upload proof of completion
    - Attach design files
    - Submit deliverables
    
    **Form data:**
    - `file`: The file to upload (required)
    - `comment`: Optional comment about the file
    """
    
    # Verify access
    job = verify_job_access(job_id, current_user, db)
    checklist = verify_checklist_access(checklist_id, job_id, db)
    
    # Verify checklist item exists and belongs to this checklist
    checklist_item = (
        db.query(ChecklistItem)
        .filter(
            ChecklistItem.id == item_id,
            ChecklistItem.checklist_id == checklist_id
        )
        .first()
    )
    
    if not checklist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist item {item_id} not found in checklist {checklist_id}"
        )
    
    # Upload file to S3
    try:
        file_content = await file.read()
        file_url = upload_file_to_s3(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )
    
    # Get or create job checklist item status
    status_record = (
        db.query(JobChecklistItemStatus)
        .filter(
            JobChecklistItemStatus.job_id == job_id,
            JobChecklistItemStatus.checklist_item_id == item_id
        )
        .first()
    )
    
    if not status_record:
        # Create new status record
        status_record = JobChecklistItemStatus(
            job_id=job_id,
            checklist_item_id=item_id,
            checked=False,
            is_approved=False
        )
        db.add(status_record)
    
    # Update status record with document link and comment
    status_record.document_link = file_url
    if comment:
        status_record.comment = comment
    
    # Commit changes
    try:
        db.commit()
        db.refresh(status_record)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update item: {str(e)}"
        )
    
    # Build response with item + status
    # item_with_status = ChecklistItemWithStatusResponse(
    #     id=checklist_item.id,
    #     document_link=status_record.document_link
    # )
    
    # return DocumentUploadResponse(
    #     success=True,
    #     message="Document uploaded successfully",
    #     item=item_with_status
    # )
    return DocumentUploadResponse(
    success=True,
    message="Document uploaded successfully",
    item={
        "id": checklist_item.id,
        "document_link": status_record.document_link
    }
)


# @router.post(
#     "/{job_id}/checklist/{checklist_id}/items/{item_id}/upload",
#     response_model=DocumentUploadResponse
# )
# async def upload_item_document(
#     job_id: int,
#     checklist_id: int,
#     item_id: int,
#     file: UploadFile = File(...),
#     comment: Optional[str] = Form(None),
#     current_user: ip = Depends(get_verified_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     📤 **DOCUMENT UPLOAD: Upload document for a checklist item**
    
#     **What this does:**
#     - Uploads file to S3 storage
#     - Updates checklist item with document URL
#     - Optionally adds/updates comment
    
#     **Supported file types:** PDF, Images, Documents
    
#     **Use cases:**
#     - Upload proof of completion
#     - Attach design files
#     - Submit deliverables
    
#     **Form data:**
#     - `file`: The file to upload (required)
#     - `comment`: Optional comment about the file
#     """
    
#     # Verify access
#     job = verify_job_access(job_id, current_user, db)
#     checklist = verify_checklist_access(checklist_id, job_id, db)
    
#     # Verify item exists
#     _, items_map = verify_checklist_items([item_id], checklist_id, db)
#     item = items_map[item_id]
    
#     # Upload file to S3
#     try:
#         file_content = await file.read()
#         file_url = upload_file_to_s3(
#             file_content=file_content,
#             filename=file.filename,
#             content_type=file.content_type
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"File upload failed: {str(e)}"
#         )
    
#     # Update item
#     item.document_link = file_url
#     if comment:
#         item.comment = comment
    
#     # Commit changes
#     try:
#         db.commit()
#         db.refresh(item)
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to update item: {str(e)}"
#         )
    
#     return DocumentUploadResponse(
#         success=True,
#         message="Document uploaded successfully",
#         item=ChecklistItemResponse.from_orm(item)
#     )


# @router.get("/{job_id}/checklists")
# async def get_job_checklists_summary(
#     job_id: int,
#     current_user: ip = Depends(get_verified_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     📋 **Get all checklists for a job with summary statistics**
    
#     **What you get:**
#     - List of all checklists for the job
#     - Summary stats for each checklist
#     - Completion percentages
#     - Item counts by status
    
#     **Use this for:**
#     - Job overview page
#     - Checklist selection screen
#     - Progress dashboard
#     """
    
#     # Verify access
#     job = verify_job_access(job_id, current_user, db)
    
#     # Fetch all checklists with items
#     checklists = get_job_checklists(job_id, db, with_items=True)
    
#     # Build response with statistics
#     checklist_summaries = []
#     for checklist in checklists:
#         # stats = calculate_checklist_stats(checklist.items)
#         job_checklist_statuses = get_job_checklist_statuses(job_id, checklist_id, db)

#         # Calculate statistics
#         stats = get_job_checklist_items_with_status(job_id, checklist.id, db)
        
#         summary = ChecklistSummaryResponse(
#             id=checklist.id,
#             name=checklist.name,
#             description=checklist.description,
#             created_at=checklist.created_at,
#             **stats
#         )
#         checklist_summaries.append(summary)
    
#     # Calculate overall job stats
#     # job_stats = calculate_job_checklists_stats(db, job_id)
    
#     return {
#         "job_id": job_id,
#         "job_title": getattr(job, 'title', f"Job {job.id}"),
#         "total_checklists": len(checklists),
#         "checklists": checklist_summaries,
#         # "overall_stats": job_stats
#     }


# @router.get("/{job_id}/checklists", response_model=JobChecklistsSummaryResponse)
# async def get_job_checklists_summary(
#     job_id: int,
#     current_user: ip = Depends(get_verified_user),  # Fixed: ip -> User
#     db: Session = Depends(get_db)
# ):
#     """
#     📋 **Get all checklists for a job with summary statistics**
    
#     **What you get:**
#     - List of all checklists for the job
#     - Summary stats for each checklist
#     - Completion percentages
#     - Item counts by status
    
#     **Use this for:**
#     - Job overview page
#     - Checklist selection screen
#     - Progress dashboard
#     """

#     # Verify access
#     job = verify_job_access(job_id, current_user, db)
    
#     # Fetch all checklists
#     checklists = get_job_checklists(job_id, db, with_items=True)
    
#     # Build response with statistics
#     checklist_summaries = []
#     for checklist in checklists:
#         # Get items with status and stats for THIS checklist
#         result = get_job_checklist_items_with_status(job_id, checklist.id, db)
        
#         # Extract stats from the result
#         stats = result["stats"]  # ✅ Get the stats dict
        
#         summary = ChecklistSummaryResponse(
#             id=checklist.id,
#             name=checklist.name,
#             description=checklist.description,
#             created_at=checklist.created_at,
#             **stats  # ✅ Now unpacks correctly
#         )
#         checklist_summaries.append(summary)
    
#     return {
#         "job_id": job_id,
#         "job_title": getattr(job, 'title', f"Job {job.id}"),
#         "total_checklists": len(checklists),
#         "checklists": checklist_summaries
#     }

@router.get("/{job_id}/checklists", response_model=JobChecklistsSummaryResponse)
async def get_job_checklists_summary(
    job_id: int,
    current_user: ip = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """
    📋 **Get all checklists for a job with summary statistics**
    """
    
    # Verify access
    job = verify_job_access(job_id, current_user, db)
    
    # Fetch all checklists
    checklists = get_job_checklists(job_id, db, with_items=True)
    
    # Build response with statistics
    checklist_summaries = []
    total_items_all = 0
    checked_count_all = 0
    
    for checklist in checklists:
        # Get items with status and stats for THIS checklist
        result = get_job_checklist_items_with_status(job_id, checklist.id, db)
        
        # Extract stats from the result
        stats = result["stats"]
        
        # Accumulate for overall stats
        total_items_all += stats["total_items"]
        checked_count_all += stats["checked_count"]
        approved_count_all += stats["approved_count"]
        
        summary = ChecklistSummaryResponse(
            id=checklist.id,
            name=checklist.name,
            description=checklist.description,
            created_at=checklist.created_at,
            **stats
        )
        checklist_summaries.append(summary)
    
    # Calculate overall completion percentage
    total_checklists_completion_percentage = (
        round((approved_count_all / total_items_all * 100), 0) 
        if total_items_all > 0 else 0.0
    )
    
    return {
        "job_id": job_id,
        "job_title": getattr(job, 'title', f"Job {job.id}"),
        "total_checklists": len(checklists),
        "total_checklists_completion_percentage": total_checklists_completion_percentage,  # ✅ Added
        "checklists": checklist_summaries
    }


# @router.get("/{job_id}/checklist/{checklist_id}/summary")
# async def get_checklist_summary(
#     job_id: int,
#     checklist_id: int,
#     current_user: ip = Depends(get_verified_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     📊 **Get checklist summary without items**
    
#     **Lightweight endpoint for:**
#     - Quick status checks
#     - Dashboard widgets
#     - Progress indicators
    
#     **Returns:** Checklist metadata + statistics only (no items)
#     """
    
#     # Verify access
#     job = verify_job_access(job_id, current_user, db)
#     checklist = verify_checklist_access(checklist_id, job_id, db)
    
#     # Get items for stats calculation
#     _, items = get_checklist_with_items(checklist_id, db)
    
#     # Calculate stats
#     stats = get_job_checklist_items_with_status(job_id, checklist_id, db)
    
#     return ChecklistSummaryResponse(
#         id=checklist.id,
#         name=checklist.name,
#         description=checklist.description,
#         created_at=checklist.created_at,
#         **stats
#     )


@router.get("/{job_id}/checklist/{checklist_id}/summary", response_model=ChecklistSummaryResponse)
async def get_checklist_summary(
    job_id: int,
    checklist_id: int,
    current_user: ip = Depends(get_verified_user),  # ✅ Fixed
    db: Session = Depends(get_db)
):
    """
    📊 **Get checklist summary without items**
    
    **Lightweight endpoint for:**
    - Quick status checks
    - Dashboard widgets
    - Progress indicators
    
    **Returns:** Checklist metadata + statistics only (no items)
    """
    
    # Verify access
    job = verify_job_access(job_id, current_user, db)
    checklist = verify_checklist_access(checklist_id, job_id, db)
    
    # Get stats (we don't need the items, just the stats)
    result = get_job_checklist_items_with_status(job_id, checklist_id, db)
    stats = result["stats"]  # ✅ Extract stats from the result dict
    
    return ChecklistSummaryResponse(
        id=checklist.id,
        name=checklist.name,
        description=checklist.description,
        created_at=checklist.created_at,
        **stats  # ✅ Now unpacks correctly: total_items, checked_count, etc.
    )


# ==================== Health Check ====================

# @router.get("/checklist/health")
# async def checklist_health_check():
#     """
#     🏥 **Health check endpoint**
    
#     Use this to verify the checklist API is operational
#     """
#     return {
#         "status": "healthy",
#         "service": "checklist-api",
#         "version": "1.0.0",
#         "features": [
#             "bulk_fetch",
#             "batch_update",
#             "document_upload",
#             "statistics"
#         ]
#     }