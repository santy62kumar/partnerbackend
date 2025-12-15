
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base


class JobMedia(Base):
    __tablename__ = "job_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("job.id"), index=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    doc_link: Mapped[str] = mapped_column(String, nullable=False)
    comment: Mapped[str] = mapped_column(String, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
