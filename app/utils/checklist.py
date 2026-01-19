"""
Utility functions for checklist database operations
Handles complex queries and business logic
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import Integer
from sqlalchemy import and_, func
from fastapi import HTTPException, status
from typing import List, Dict, Tuple, Optional

from app.model.job import Job
from app.model.checklist import Checklist, ChecklistItem
from app.model.ip import ip


# ==================== Validation Functions ====================

def verify_job_access(job_id: int, current_user: ip, db: Session) -> Job:
    """
    Verify that the job exists and user has access to it
    
    Args:
        job_id: ID of the job to verify
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Job object if found and accessible
    
    Raises:
        HTTPException: If job not found or user lacks access
    """
    job = db.query(Job).filter(
        and_(
            Job.id == job_id,
            Job.assigned_ip_id == current_user.id
        )
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or you don't have access to it"
        )
    
    return job


def verify_checklist_access(
    checklist_id: int, 
    job_id: int, 
    db: Session
) -> Checklist:
    """
    Verify that the checklist exists and belongs to the job
    
    Args:
        checklist_id: ID of the checklist
        job_id: ID of the job
        db: Database session
    
    Returns:
        Checklist object if found and belongs to job
    
    Raises:
        HTTPException: If checklist not found or doesn't belong to job
    """
    checklist = (
        db.query(Checklist)
        .join(Checklist.jobs)
        .filter(
            and_(
                Checklist.id == checklist_id,
                Job.id == job_id
            )
        )
        .first()
    )
    
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checklist not found or doesn't belong to this job"
        )
    
    return checklist


def verify_checklist_items(
    item_ids: List[int],
    checklist_id: int,
    db: Session
) -> Tuple[List[ChecklistItem], Dict[int, ChecklistItem]]:
    """
    Verify that all items exist and belong to the checklist
    
    Args:
        item_ids: List of item IDs to verify
        checklist_id: ID of the checklist
        db: Database session
    
    Returns:
        Tuple of (list of items, dict mapping item_id to item)
    
    Raises:
        HTTPException: If any items are missing or don't belong to checklist
    """
    items = (
        db.query(ChecklistItem)
        .filter(
            and_(
                ChecklistItem.id.in_(item_ids),
                ChecklistItem.checklist_id == checklist_id
            )
        )
        .all()
    )
    
    if len(items) != len(item_ids):
        found_ids = {item.id for item in items}
        missing_ids = set(item_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Items not found or don't belong to this checklist: {list(missing_ids)}"
        )
    
    items_map = {item.id: item for item in items}
    return items, items_map


# ==================== Statistics Functions ====================

def calculate_checklist_stats(items: List[ChecklistItem]) -> Dict[str, any]:
    """
    Calculate statistics for checklist items
    
    Args:
        items: List of checklist items
    
    Returns:
        Dictionary with statistics:
        - total_items: Total number of items
        - checked_count: Number of checked items
        - pending_count: Number of pending items
        - approved_count: Number of approved items
        - completion_percentage: Percentage of checked items
    """
    total = len(items)
    
    if total == 0:
        return {
            "total_items": 0,
            "checked_count": 0,
            "pending_count": 0,
            "approved_count": 0,
            "completion_percentage": 0.0
        }
    
    checked = sum(1 for item in items if item.checked)
    pending = sum(1 for item in items if item.status == "pending")
    approved = sum(1 for item in items if item.status == "approved")
    
    completion_percentage = round((checked / total) * 100, 2)
    
    return {
        "total_items": total,
        "checked_count": checked,
        "pending_count": pending,
        "approved_count": approved,
        "completion_percentage": completion_percentage
    }


def calculate_job_checklists_stats(db: Session, job_id: int) -> Dict[str, any]:
    """
    Calculate aggregate statistics for all checklists in a job
    
    Args:
        db: Database session
        job_id: ID of the job
    
    Returns:
        Dictionary with aggregate statistics
    """
    # Query to get aggregated stats
    # stats = (
    #     db.query(
    #         func.count(ChecklistItem.id).label('total_items'),
    #         func.sum(func.cast(ChecklistItem.checked, Integer)).label('checked_items'),
    #         func.sum(
    #             func.case(
    #                 (ChecklistItem.status == 'pending', 1),
    #                 else_=0
    #             )
    #         ).label('pending_items'),
    #         func.sum(
    #             func.case(
    #                 (ChecklistItem.status == 'approved', 1),
    #                 else_=0
    #             )
    #         ).label('approved_items')
    #     )
    #     .join(Checklist, ChecklistItem.checklist_id == Checklist.id)
    #     .join(Checklist.jobs)
    #     .filter(Job.id == job_id)
    #     .first()
    # )


    stats = (
    db.query(
        func.count(ChecklistItem.id).label('total_items'),
        func.sum(func.cast(ChecklistItem.checked, Integer)).label('checked_items'),
        func.sum(
            func.case(
                [(ChecklistItem.status == 'pending', 1)],  # Use list syntax for conditionals
                else_=0
            )
        ).label('pending_items'),
        func.sum(
            func.case(
                [(ChecklistItem.status == 'approved', 1)],  # Use list syntax for conditionals
                else_=0
            )
        ).label('approved_items')
    )
    .join(Checklist, ChecklistItem.checklist_id == Checklist.id)
    .join(Checklist.jobs)
    .filter(Job.id == job_id)
    .first()
    )

    

    
    total = stats.total_items or 0
    checked = stats.checked_items or 0
    
    completion_percentage = round((checked / total) * 100, 2) if total > 0 else 0.0
    
    return {
        "total_items": total,
        "checked_count": checked,
        "pending_count": stats.pending_items or 0,
        "approved_count": stats.approved_items or 0,
        "completion_percentage": completion_percentage
    }


# ==================== Query Functions ====================

def get_checklist_with_items(
    checklist_id: int,
    db: Session
) -> Tuple[Checklist, List[ChecklistItem]]:
    """
    Fetch checklist with all its items in an optimized query
    
    Args:
        checklist_id: ID of the checklist
        db: Database session
    
    Returns:
        Tuple of (checklist, list of items ordered by position)
    """
    # Fetch checklist with eager loading of items
    checklist = (
        db.query(Checklist)
        .options(joinedload(Checklist.items))
        .filter(Checklist.id == checklist_id)
        .first()
    )
    
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checklist not found"
        )
    
    # Sort items by position
    items = sorted(checklist.items, key=lambda x: x.position)
    
    return checklist, items


def get_job_checklists(
    job_id: int,
    db: Session,
    with_items: bool = False
) -> List[Checklist]:
    """
    Fetch all checklists for a job
    
    Args:
        job_id: ID of the job
        db: Database session
        with_items: Whether to eager load items
    
    Returns:
        List of checklists
    """
    query = db.query(Checklist).join(Checklist.jobs).filter(Job.id == job_id)
    
    if with_items:
        query = query.options(joinedload(Checklist.items))
    
    return query.all()


# ==================== Batch Update Functions ====================

def apply_batch_updates(
    items_map: Dict[int, ChecklistItem],
    updates: List[Dict],
    db: Session
) -> List[ChecklistItem]:
    """
    Apply batch updates to checklist items
    
    Args:
        items_map: Dictionary mapping item IDs to item objects
        updates: List of update dictionaries
        db: Database session
    
    Returns:
        List of updated items
    
    Raises:
        HTTPException: If validation fails or update fails
    """
    valid_statuses = ["update", "pending", "approved"]
    updated_items = []
    
    try:
        for update_data in updates:
            item_id = update_data.get('id')
            item = items_map.get(item_id)
            
            if not item:
                continue
            
            # Update fields that are provided
            if 'checked' in update_data and update_data['checked'] is not None:
                item.checked = update_data['checked']
            
            if 'status' in update_data and update_data['status'] is not None:
                status_value = update_data['status']
                if status_value not in valid_statuses:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid status '{status_value}'. Must be one of: {valid_statuses}"
                    )
                item.status = status_value
            
            if 'comment' in update_data and update_data['comment'] is not None:
                item.comment = update_data['comment']
            
            if 'document_link' in update_data and update_data['document_link'] is not None:
                item.document_link = update_data['document_link']
            
            updated_items.append(item)
        
        # Commit all changes
        db.commit()
        
        # Refresh all items
        for item in updated_items:
            db.refresh(item)
        
        return updated_items
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update items: {str(e)}"
        )


# ==================== Status Validation ====================

def validate_status_transition(
    current_status: str,
    new_status: str
) -> bool:
    """
    Validate if status transition is allowed
    
    Args:
        current_status: Current item status
        new_status: New status to transition to
    
    Returns:
        True if transition is allowed
    
    This can be extended to enforce specific workflow rules
    For example:
    - update -> pending (allowed)
    - pending -> approved (allowed)
    - approved -> update (not allowed)
    """
    # Define allowed transitions
    allowed_transitions = {
        "update": ["pending", "approved"],
        "pending": ["approved", "update"],
        "approved": ["update"]  # Allow going back for corrections
    }
    
    # If same status, always allowed
    if current_status == new_status:
        return True
    
    # Check if transition is in allowed list
    return new_status in allowed_transitions.get(current_status, [])