import os
import threading
from dotenv import load_dotenv

from core.queue.db import init_db
from core.queue.queue import enqueue_download
from core.worker import worker_loop
from web.web import app  # Import the Flask app

if __name__ == "__main__":
    print("[Main] Loading environment...")
    load_dotenv()

    print("[Main] Initializing database...")
    init_db()

    # Optional: enqueue an example URL
    example_reel_url = "https://www.youtube.com/shorts/K4cxoowc46E"
    # enqueue_download(example_reel_url)

    # ✅ Only run this in the actual reloaded process
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        print("[Main] Starting worker loop in background thread...")

        def start_worker():
            try:
                worker_loop()
            except Exception as e:
                print(f"[Worker] Error: {e}")

        threading.Thread(target=start_worker, daemon=True).start()

    print("[Main] Starting Flask app...")
    app.run(debug=True, host="0.0.0.0", port=5050)
