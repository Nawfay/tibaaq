
import os
from core.queue.db import init_db
from core.queue.queue import enqueue_download
from core.worker import worker_loop

from dotenv import load_dotenv

if __name__ == "__main__":
    print("[Main] Loading environment...")
    load_dotenv()  # Load TANDOOR_API_URL, TANDOOR_API_TOKEN, GROQ_API_KEY, etc.

    print("[Main] Initializing database...")
    init_db()

    # Example Reel URL (public)
    example_reel_url = "https://www.tiktok.com/@fortheloveofspice/video/7359625866558672174"
    
    print(f"[Main] Enqueuing example URL: {example_reel_url}")
    enqueue_download(example_reel_url)

    print("[Main] Starting worker loop...")
    worker_loop()
