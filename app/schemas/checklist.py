"""
Pydantic schemas for Checklist API
Separating schemas for better organization and reusability
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


# ==================== Response Schemas ====================

class ChecklistItemResponse(BaseModel):
    """Schema for checklist item in API responses"""
    id: int
    checklist_id: int
    text: str
    status: str
    position: int
    checked: bool
    comment: Optional[str] = None
    document_link: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True  # For SQLAlchemy ORM compatibility
        json_schema_extra = {
            "example": {
                "id": 1,
                "checklist_id": 1,
                "text": "Complete design mockups",
                "status": "pending",
                "position": 1,
                "checked": False,
                "comment": "Waiting for client feedback",
                "document_link": "https://s3.amazonaws.com/...",
                "created_at": "2025-01-15T10:30:00"
            }
        }


class ChecklistResponse(BaseModel):
    """Schema for checklist metadata"""
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Website Development Checklist",
                "description": "Complete checklist for web development projects",
                "created_at": "2025-01-15T10:30:00"
            }
        }


class ChecklistSummaryResponse(BaseModel):
    """Schema for checklist with summary statistics"""
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    total_items: int
    checked_count: int
    pending_count: int
    approved_count: int
    completion_percentage: float

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Website Development Checklist",
                "description": "Complete checklist for web development projects",
                "created_at": "2025-01-15T10:30:00",
                "total_items": 10,
                "checked_count": 7,
                "pending_count": 2,
                "approved_count": 5,
                "completion_percentage": 70.0
            }
        }


class BulkChecklistResponse(BaseModel):
    """Schema for complete checklist with all items (bulk fetch response)"""
    job_id: int
    job_title: str
    checklist: ChecklistResponse
    items: List[ChecklistItemResponse]
    total_items: int
    checked_count: int
    pending_count: int
    approved_count: int
    completion_percentage: float

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": 123,
                "job_title": "E-commerce Website Redesign",
                "checklist": {
                    "id": 1,
                    "name": "Development Checklist",
                    "description": "All development tasks",
                    "created_at": "2025-01-15T10:30:00"
                },
                "items": [],
                "total_items": 10,
                "checked_count": 7,
                "pending_count": 2,
                "approved_count": 5,
                "completion_percentage": 70.0
            }
        }


# ==================== Request Schemas ====================

class ChecklistItemUpdateRequest(BaseModel):
    """Schema for updating a single checklist item"""
    id: int = Field(..., description="ID of the item to update", gt=0)
    checked: Optional[bool] = Field(None, description="Checkbox state")
    status: Optional[str] = Field(None, description="Status: update, pending, or approved")
    comment: Optional[str] = Field(None, description="Comment or remarks", max_length=1000)
    document_link: Optional[str] = Field(None, description="URL to uploaded document", max_length=500)

    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["update", "pending", "approved"]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "checked": True,
                "status": "approved",
                "comment": "Completed and reviewed",
                "document_link": "https://s3.amazonaws.com/..."
            }
        }


class BatchUpdateRequest(BaseModel):
    """Schema for batch updating multiple checklist items"""
    updates: List[ChecklistItemUpdateRequest] = Field(
        ..., 
        min_items=1,
        max_items=100,  # Prevent abuse
        description="List of item updates to apply"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "updates": [
                    {
                        "id": 1,
                        "checked": True,
                        "comment": "Completed"
                    },
                    {
                        "id": 2,
                        "status": "approved"
                    },
                    {
                        "id": 3,
                        "checked": False,
                        "document_link": "https://s3.amazonaws.com/..."
                    }
                ]
            }
        }


class BatchUpdateResponse(BaseModel):
    """Schema for batch update response"""
    success: bool
    message: str
    updated_count: int
    items: List[ChecklistItemResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully updated 3 items",
                "updated_count": 3,
                "items": []
            }
        }


# ==================== Document Upload Schemas ====================

class DocumentUploadResponse(BaseModel):
    """Schema for document upload response"""
    success: bool
    message: str
    item: ChecklistItemResponse

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Document uploaded successfully",
                "item": {
                    "id": 1,
                    "checklist_id": 1,
                    "text": "Upload design files",
                    "status": "pending",
                    "position": 1,
                    "checked": True,
                    "comment": "Design v2.0",
                    "document_link": "https://s3.amazonaws.com/...",
                    "created_at": "2025-01-15T10:30:00"
                }
            }
        }


# ==================== Error Response Schemas ====================

class ErrorResponse(BaseModel):
    """Standard error response schema"""
    detail: str
    error_code: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Checklist not found or doesn't belong to this job",
                "error_code": "CHECKLIST_NOT_FOUND"
            }
        }