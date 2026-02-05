from sqlalchemy import Column, Integer, String, Boolean, Numeric, Date, ForeignKey
from sqlalchemy.orm import  Mapped, mapped_column, relationship
from app.database import Base
from decimal import Decimal
from datetime import date
from app.model.associations import JobChecklist




# Define the Job-Checklist Link table first


class Job(Base):
    __tablename__ = "job"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    customer_name: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="created")
    pincode: Mapped[int] = mapped_column(Integer)
    assigned_ip_id: Mapped[int] = mapped_column(Integer, nullable=True)
    type: Mapped[str] = mapped_column(String)
    rate: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    size: Mapped[int] = mapped_column(Integer, nullable=True)
    delivery_date: Mapped[date] = mapped_column(Date)
    checklist_link: Mapped[str] = mapped_column(String, nullable=True)
    google_map_link: Mapped[str] = mapped_column(String, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=True)

    job_checklists: Mapped["JobChecklist"] = relationship(
        "JobChecklist", back_populates="job"
    )
    
    checklists: Mapped[list["Checklist"]] = relationship(
        "Checklist",
        secondary=JobChecklist.__table__,  # Use JobChecklist.__table__ instead of the class itself
        back_populates="jobs",
        lazy="select"
    )
    # job_checklists: Mapped["JobChecklist"] = relationship(
    #         "JobChecklist", back_populates="job"
    #     )


    job_checklist_item_statuses: Mapped[list["JobChecklistItemStatus"]] = relationship(
        "JobChecklistItemStatus",
        back_populates="job",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Job {self.name}>"
    
                            

   
    
