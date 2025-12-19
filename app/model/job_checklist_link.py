from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class JobChecklistLink(Base):
    __tablename__ = "job_checklist_link"

    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id"), primary_key=True)
    checklist_id: Mapped[int] = mapped_column(Integer, ForeignKey("checklists.id"), primary_key=True)
