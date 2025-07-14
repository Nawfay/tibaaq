# core/queue/models.

from sqlalchemy import Column, String, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum as PyEnum


Base = declarative_base()

class TaskStatus(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    INGESTING = "ingesting"
    DONE = "done"
    FAILED = "failed"

class DownloadTask(Base):
    __tablename__ = "download_tasks"

    id = Column(String, primary_key=True)
    url = Column(Text, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    requester = Column(String, nullable=True)
