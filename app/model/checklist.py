# """
# app/model/checklist.py

# Updated to import association table from separate file
# """

# from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Text
# from sqlalchemy import func

# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from datetime import datetime
# from app.database import Base
# from app.model.associations import JobChecklist  # ✅ Import the table
# # from sqlalchemy import Integer



# class Checklist(Base):
#     """Checklist Model"""
#     __tablename__ = "checklists"
    
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
#     name: Mapped[str] = mapped_column(String(255), nullable=False)
#     description: Mapped[str | None] = mapped_column(Text, nullable=True)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
#     updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    
#     # job_checklists: Mapped["JobChecklist"] = relationship(
#     #     "JobChecklist", back_populates="checklist"
#     # )
#     job_checklists: Mapped[list["JobChecklist"]] = relationship(
#     "JobChecklist",
#     back_populates="checklist",
#     cascade="all, delete-orphan"
# )


#     # Many-to-many relationship with Job via JobChecklist
#     # jobs: Mapped[list["Job"]] = relationship(
#     #     "Job",
#     #     secondary=JobChecklist.__table__,  # Use JobChecklist.__table__ instead of the class itself
#     #     back_populates="checklists",
#     #     lazy="select"
#     # )

#     jobs: Mapped[list["Job"]] = relationship(
#     "Job",
#     secondary=JobChecklist.__table__,
#     back_populates="checklists",
#     lazy="select",
#     viewonly=True   # 👈 IMPORTANT
# )

#     items: Mapped[list["ChecklistItem"]] = relationship(
#         "ChecklistItem",
#         back_populates="checklist",
#         cascade="all, delete-orphan",
#         lazy="select",
#         order_by="ChecklistItem.position"
#     )
    
#     def __repr__(self):
#         return f"<Checklist(id={self.id}, name='{self.name}')>"


# class ChecklistItem(Base):
#     """ChecklistItem Model"""
#     __tablename__ = "checklist_items"
    
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
#     checklist_id: Mapped[int] = mapped_column(Integer, ForeignKey("checklists.id", ondelete="CASCADE"), nullable=False, index=True)
#     text: Mapped[str] = mapped_column(Text, nullable=False)
#     status: Mapped[str] = mapped_column(String(50), default="update", nullable=False, index=True)
#     position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
#     checked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
#     comment: Mapped[str | None] = mapped_column(Text, nullable=True)
#     document_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
#     updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
#     # Relationship
#     checklist: Mapped["Checklist"] = relationship(
#         "Checklist",
#         back_populates="items",
#         lazy="select"
#     )
    
#     def __repr__(self):
#         return f"<ChecklistItem(id={self.id}, text='{self.text[:30]}...', status='{self.status}')>"


from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.model.associations import JobChecklist 

from app.database import Base




class Checklist(Base):
    """Checklist Model"""
    __tablename__ = "checklists"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    
    # job_checklists: Mapped["JobChecklist"] = relationship(
    #     "JobChecklist", back_populates="checklist"
    # )
    job_checklists: Mapped[list["JobChecklist"]] = relationship(
    "JobChecklist",
    back_populates="checklist",
    cascade="all, delete-orphan"
)


    # Many-to-many relationship with Job via JobChecklist
    # jobs: Mapped[list["Job"]] = relationship(
    #     "Job",
    #     secondary=JobChecklist.__table__,  # Use JobChecklist.__table__ instead of the class itself
    #     back_populates="checklists",
    #     lazy="select"
    # )

    jobs: Mapped[list["Job"]] = relationship(
    "Job",
    secondary=JobChecklist.__table__,
    back_populates="checklists",
    lazy="select",
    viewonly=True   # 👈 IMPORTANT
)

    items: Mapped[list["ChecklistItem"]] = relationship(
        "ChecklistItem",
        back_populates="checklist",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="ChecklistItem.position"
    )
    
    def __repr__(self):
        return f"<Checklist(id={self.id}, name='{self.name}')>"



class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    checklist_id: Mapped[int] = mapped_column(ForeignKey("checklists.id"))
    text: Mapped[str] = mapped_column(String)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    # checklist: Mapped["Checklist"] = relationship(
    #     "Checklist", back_populates="checklist_items"
    # )

    checklist: Mapped["Checklist"] = relationship(
        "Checklist", back_populates="items"  # ✅ Changed to "items"
    )

    job_checklist_item_statuses: Mapped[List["JobChecklistItemStatus"]] = relationship(
        "JobChecklistItemStatus", back_populates="checklist_item"
    )


class JobChecklistItemStatus(Base):
    __tablename__ = "job_checklist_item_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job.id"))
    checklist_item_id: Mapped[int] = mapped_column(ForeignKey("checklist_items.id"))
    checked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    admin_comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    document_link: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="job_checklist_item_statuses")
    checklist_item: Mapped["ChecklistItem"] = relationship(
        "ChecklistItem", back_populates="job_checklist_item_statuses"
    )


   