

"""
app/model/associations.py
"""

import datetime

from sqlalchemy import Table, Column, Integer, ForeignKey
from app.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, func   



class JobChecklist(Base):
    __tablename__ = "job_checklists"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job.id"))
    checklist_id: Mapped[int] = mapped_column(ForeignKey("checklists.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    job: Mapped["Job"] = relationship("Job", back_populates="job_checklists")
    checklist: Mapped["Checklist"] = relationship(
        "Checklist", back_populates="job_checklists"
    )