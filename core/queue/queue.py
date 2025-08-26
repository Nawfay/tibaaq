# core/queue/queue.py

import uuid
from core.queue.models import DownloadTask, TaskStatus
from core.queue.db import SessionLocal
from core.utils import Colors

def enqueue_download(url: str, requester: str = None):
    session = SessionLocal()
    task = DownloadTask(id=str(uuid.uuid4()), url=url, status=TaskStatus.PENDING, requester=requester)
    session.add(task)
    session.commit()
    session.close()
    print(f"{Colors.QUEUE} Enqueued download task: {url}")

