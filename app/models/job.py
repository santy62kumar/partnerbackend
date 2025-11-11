from sqlalchemy import Column, Integer, String, Numeric, Date, column
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Job(Base):
    __tablename__ = "job"

    id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    name = Column(String)                        # job name (Full Kitchen, Wardrobe, etc.)
    customer_name = Column(String)
    address = Column(String)
    city = Column(String)
    status = Column(String, default="created")                   # created/in-progress/completed/paused
    pincode = Column(Integer)
    assigned_ip_id = Column(Integer, nullable=True)
    type = Column(String)                                        # kitchen / wardrobe / pantry etc
    rate = Column(Numeric(10,2))
    size = Column(Integer,nullable=True)                                       # size (sqft or custom unit)
    delivery_date = Column(Date)
    checklist_link = Column(String, nullable=True) 
    
    
    def __repr__(self):
        return f"<Job {self.name}>"
    
                                 # JSON string for checklist items

   
    
