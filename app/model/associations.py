# # from sqlalchemy import Table, Column, Integer, ForeignKey, DateTime
# # from datetime import datetime
# # from app.database import Base


# # # Job <-> Checklist many-to-many association
# # job_checklist_link = Table(
# #     'job_checklist_link',
# #     Base.metadata,
# #     Column('job_id', Integer, ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True),
# #     Column('checklist_id', Integer, ForeignKey('checklists.id', ondelete='CASCADE'), primary_key=True),
# #     Column('created_at', DateTime, default=datetime.utcnow)
# # )

# """
# app/model/associations.py

# Association tables for many-to-many relationships.

# IMPORTANT: This file should be imported AFTER the model classes are defined,
# but the Table objects will be created when the models reference them.
# """

# from sqlalchemy import Table, Column, Integer, ForeignKey, DateTime
# from datetime import datetime


# def create_job_checklist_link(metadata):
#     """
#     Create job_checklist_link table.
#     Call this function after Base.metadata is available.
#     """
#     return Table(
#         'job_checklist_link',
#         metadata,
#         Column('job_id', Integer, ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True),
#         Column('checklist_id', Integer, ForeignKey('checklists.id', ondelete='CASCADE'), primary_key=True),
#         Column('created_at', DateTime, default=datetime.utcnow)
#     )


# # This will be set by the models
# job_checklist_link = None


"""
app/model/associations.py
"""

from sqlalchemy import Table, Column, Integer, ForeignKey
from app.database import Base

job_checklist_link = Table(
    'job_checklist_link',
    Base.metadata,
    Column('job_id', Integer, ForeignKey('job.id', ondelete="CASCADE"), primary_key=True),  # ✅ Changed from 'jobs.id' to 'job.id'
    Column('checklist_id', Integer, ForeignKey('checklists.id', ondelete="CASCADE"), primary_key=True)
)