"""
app/model/checklist.py

Updated to import association table from separate file
"""

from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base
from app.model.associations import job_checklist_link  # ✅ Import the table


class Checklist(Base):
    """Checklist Model"""
    __tablename__ = "checklists"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    jobs: Mapped[list["Job"]] = relationship(
        "Job",
        secondary=job_checklist_link,  # ✅ Use the imported table object
        back_populates="checklists",
        lazy="select"
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
    """ChecklistItem Model"""
    __tablename__ = "checklist_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    checklist_id: Mapped[int] = mapped_column(Integer, ForeignKey("checklists.id", ondelete="CASCADE"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="update", nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    checked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    checklist: Mapped["Checklist"] = relationship(
        "Checklist",
        back_populates="items",
        lazy="select"
    )
    
    def __repr__(self):
        return f"<ChecklistItem(id={self.id}, text='{self.text[:30]}...', status='{self.status}')>"