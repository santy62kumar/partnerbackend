from sqlalchemy.orm import Session
from app.model.so_detail import SODetail
from app.model.site_requisite import SiteRequisite
from app.schemas.requisite_schema import SiteRequisiteSubmit
from datetime import datetime
from typing import List

class RequisiteService:
    
    @staticmethod
    def submit_site_requisite(db: Session, data: SiteRequisiteSubmit):
        """Submit site requisite with all bucket items"""
        
        # Check if SO already exists
        so_detail = db.query(SODetail).filter(
            SODetail.sales_order == data.sales_order
        ).first()
        
        # Create new SO if doesn't exist
        if not so_detail:
            so_detail = SODetail(
                sales_order=data.sales_order,
                sr_poc=data.sr_poc,
                status="pending"
            )
            db.add(so_detail)
            db.flush()  # Get the ID without committing
        
        # Add all requisite items
        for item in data.items:
            site_req = SiteRequisite(
                so_detail_id=so_detail.id,
                product_name=item.product_name,
                quantity=item.quantity,
                issue_description=item.issue_description,
                responsible_department=item.responsible_department
            )
            db.add(site_req)
        
        db.commit()
        db.refresh(so_detail)
        
        return so_detail
    
    @staticmethod
    def get_history(db: Session, limit: int = 50, offset: int = 0) -> List[SODetail]:
        """Get all site requisite history"""
        return db.query(SODetail).order_by(
            SODetail.created_date.desc()
        ).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_history_by_sales_order(db: Session, sales_order: str):
        """Get history for specific sales order"""
        return db.query(SODetail).filter(
            SODetail.sales_order == sales_order
        ).first()
    
    @staticmethod
    def update_status(db: Session, so_id: int, status: str):
        """Update SO status"""
        so_detail = db.query(SODetail).filter(SODetail.id == so_id).first()
        if so_detail:
            so_detail.status = status
            if status == "completed":
                so_detail.closed_date = datetime.utcnow()
            db.commit()
            db.refresh(so_detail)
        return so_detail