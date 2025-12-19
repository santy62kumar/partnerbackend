# from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey
# from sqlalchemy.orm import Mapped, mapped_column, relationship
# from datetime import datetime
# from app.database import Base
# # from app.model.checklist import Checklist
# from app.model.associations import job_checklist_link

# class ChecklistItem(Base):
#     __tablename__ = "checklist_items"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
#     checklist_id: Mapped[int] = mapped_column(Integer, ForeignKey("checklists.id"), index=True)
#     text: Mapped[str] = mapped_column(String, nullable=False)
#     status: Mapped[str] = mapped_column(String, default="pending")  # e.g., 'pending', 'approved'
#     position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
#     checked: Mapped[bool] = mapped_column(Boolean, default=False)
#     comment: Mapped[str] = mapped_column(String, nullable=True)
#     document_link: Mapped[str | None] = mapped_column(String, nullable=True)
#     created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

#     # Relationship with the Checklist
#     checklist: Mapped["Checklist"] = relationship("Checklist", back_populates="items")
