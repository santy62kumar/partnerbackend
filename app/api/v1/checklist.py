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
from app.model.checklist import Checklist

# Import schemas
from app.schemas.checklist import (
    BulkChecklistResponse,
    ChecklistResponse,
    ChecklistItemResponse,
    ChecklistSummaryResponse,
    BatchUpdateRequest,
    BatchUpdateResponse,
    DocumentUploadResponse
)

# Import utilities
from app.utils.checklist import (
    verify_job_access,
    verify_checklist_access,
    verify_checklist_items,
    calculate_checklist_stats,
    calculate_job_checklists_stats,
    get_checklist_with_items,
    get_job_checklists,
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
    """
    📥 **BULK FETCH: Get complete checklist with all items**
    
    **Single optimized query that fetches:**
    - Job details
    - Checklist metadata  
    - All checklist items (ordered by position)
    - Statistics (checked, pending, approved counts)
    
    **Use this endpoint to:**
    - Load the checklist page
    - Get complete state in one request
    - Avoid multiple round trips
    
    **Response includes:**
    - Complete checklist data
    - All items with their current state
    - Aggregate statistics
    - Completion percentage
    
    **Performance:** Single database query with JOIN
    """
    
    # Verify access
    job = verify_job_access(job_id, current_user, db)
    checklist = verify_checklist_access(checklist_id, job_id, db)
    
    # Fetch items with optimized query
    _, items = get_checklist_with_items(checklist_id, db)
    
    # Calculate statistics
    stats = calculate_checklist_stats(items)
    
    # Build response
    return BulkChecklistResponse(
        job_id=job.id,
        job_title=getattr(job, 'title', f"Job {job.id}"),
        checklist=ChecklistResponse.from_orm(checklist),
        items=[ChecklistItemResponse.from_orm(item) for item in items],
        **stats
    )


@router.post("/{job_id}/checklist/{checklist_id}/update", response_model=BatchUpdateResponse)
async def batch_update_items(
    job_id: int,
    checklist_id: int,
    batch_request: BatchUpdateRequest,
    current_user: ip = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """
    💾 **BATCH UPDATE: Update multiple checklist items atomically**
    
    **What this does:**
    - Accepts multiple item updates in one request
    - Validates all items belong to the checklist
    - Performs atomic update (all succeed or all fail)
    - Returns updated items
    
    **Request body example:**
    ```json
    {
        "updates": [
            {"id": 1, "checked": true, "comment": "Done"},
            {"id": 2, "status": "approved"},
            {"id": 3, "checked": false, "document_link": "https://..."}
        ]
    }
    ```
    
    **Benefits:**
    - Reduced network calls (N requests → 1 request)
    - Atomic transaction (data consistency)
    - Optimistic UI support
    - Better performance
    
    **Status values:** `update`, `pending`, `approved`
    
    **Transaction safety:** Uses database transaction - if any update fails, all changes are rolled back
    """
    
    # Verify access
    job = verify_job_access(job_id, current_user, db)
    checklist = verify_checklist_access(checklist_id, job_id, db)
    
    # Extract item IDs
    item_ids = [update.id for update in batch_request.updates]
    
    # Verify all items exist and belong to checklist
    _, items_map = verify_checklist_items(item_ids, checklist_id, db)
    
    # Convert Pydantic models to dicts for processing
    updates_dict = [update.dict(exclude_none=True) for update in batch_request.updates]
    
    # Apply batch updates
    updated_items = apply_batch_updates(items_map, updates_dict, db)
    
    # Return response
    return BatchUpdateResponse(
        success=True,
        message=f"Successfully updated {len(updated_items)} item(s)",
        updated_count=len(updated_items),
        items=[ChecklistItemResponse.from_orm(item) for item in updated_items]
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
    current_user: ip = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """
    📤 **DOCUMENT UPLOAD: Upload document for a checklist item**
    
    **What this does:**
    - Uploads file to S3 storage
    - Updates checklist item with document URL
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
    
    # Verify item exists
    _, items_map = verify_checklist_items([item_id], checklist_id, db)
    item = items_map[item_id]
    
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
    
    # Update item
    item.document_link = file_url
    if comment:
        item.comment = comment
    
    # Commit changes
    try:
        db.commit()
        db.refresh(item)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update item: {str(e)}"
        )
    
    return DocumentUploadResponse(
        success=True,
        message="Document uploaded successfully",
        item=ChecklistItemResponse.from_orm(item)
    )


@router.get("/{job_id}/checklists")
async def get_job_checklists_summary(
    job_id: int,
    current_user: ip = Depends(get_verified_user),
    db: Session = Depends(get_db)
):
    """
    📋 **Get all checklists for a job with summary statistics**
    
    **What you get:**
    - List of all checklists for the job
    - Summary stats for each checklist
    - Completion percentages
    - Item counts by status
    
    **Use this for:**
    - Job overview page
    - Checklist selection screen
    - Progress dashboard
    """
    
    # Verify access
    job = verify_job_access(job_id, current_user, db)
    
    # Fetch all checklists with items
    checklists = get_job_checklists(job_id, db, with_items=True)
    
    # Build response with statistics
    checklist_summaries = []
    for checklist in checklists:
        stats = calculate_checklist_stats(checklist.items)
        
        summary = ChecklistSummaryResponse(
            id=checklist.id,
            name=checklist.name,
            description=checklist.description,
            created_at=checklist.created_at,
            **stats
        )
        checklist_summaries.append(summary)
    
    # Calculate overall job stats
    job_stats = calculate_job_checklists_stats(db, job_id)
    
    return {
        "job_id": job_id,
        "job_title": getattr(job, 'title', f"Job {job.id}"),
        "total_checklists": len(checklists),
        "checklists": checklist_summaries,
        "overall_stats": job_stats
    }


@router.get("/{job_id}/checklist/{checklist_id}/summary")
async def get_checklist_summary(
    job_id: int,
    checklist_id: int,
    current_user: ip = Depends(get_verified_user),
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
    
    # Get items for stats calculation
    _, items = get_checklist_with_items(checklist_id, db)
    
    # Calculate stats
    stats = calculate_checklist_stats(items)
    
    return ChecklistSummaryResponse(
        id=checklist.id,
        name=checklist.name,
        description=checklist.description,
        created_at=checklist.created_at,
        **stats
    )


# ==================== Health Check ====================

@router.get("/checklist/health")
async def checklist_health_check():
    """
    🏥 **Health check endpoint**
    
    Use this to verify the checklist API is operational
    """
    return {
        "status": "healthy",
        "service": "checklist-api",
        "version": "1.0.0",
        "features": [
            "bulk_fetch",
            "batch_update",
            "document_upload",
            "statistics"
        ]
    }