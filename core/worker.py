import os
import time
from core.queue.db import SessionLocal
from core.queue.models import DownloadTask, TaskStatus
from core.ingestion.downloader import download_video_and_metadata
from core.ingestion.transcription import transcribe_audio
from core.process import generate_recipe_json
from core.external.tandoor import push_recipe_to_tandoor, upload_tandoor_image

def clear_tmp_files():
    tmp_dir = "tmp"
    for filename in os.listdir(tmp_dir):
        file_path = os.path.join(tmp_dir, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

def process_task(task: DownloadTask, session):
    print(f"[Worker] Processing task: {task.id} - {task.url}")
    task.status = TaskStatus.INGESTING
    session.commit()

    try:
        # Step 1: Download video and get metadata
        file_path, metadata = download_video_and_metadata(task.url, task.id)
        print(f"[Worker] Downloaded: {file_path}")

        # Step 2: Transcribe audio
        transcript = transcribe_audio(file_path)
        print("[Worker] Transcription complete.")

        # Step 3: Generate recipe JSON using LLM
        description = metadata["description"]
        source_url = task.url
        recipe_json = generate_recipe_json(description, transcript, source_url)
        print("[Worker] Recipe JSON generated.")

        # Step 4: Push to Tandoor
        result = push_recipe_to_tandoor(recipe_json)
        # print(result)
        print(file_path[:-4] + ".jpg")
        upload_tandoor_image(result["id"], file_path[:-4] + ".jpg")
        
        print("[Worker] Recipe pushed to Tandoor.")

        task.status = TaskStatus.DONE
        session.commit()

        clear_tmp_files()

        
    except Exception as e:
        print(f"[Worker] Task {task.id} failed: {type(e).__name__}: {e}")
        task.status = TaskStatus.FAILED
        session.commit()

def worker_loop(poll_interval=5):
    print("[Worker] Starting worker loop...")
    while True:
        session = SessionLocal()
        task = session.query(DownloadTask).filter_by(status=TaskStatus.PENDING).first()
        if task:
            process_task(task, session)
        else:
            session.close()
            print("[Worker] No pending tasks. Sleeping...")
            time.sleep(poll_interval)
