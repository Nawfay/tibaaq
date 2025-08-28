# main.py

import os
import threading
from dotenv import load_dotenv

from core.queue.db import init_db
from core.queue.queue import enqueue_download
from core.worker import worker_loop
from web.web import app
from core.utils import Colors
from core.config import INSTAGRAM_ENABLED, DISCORD_ENABLED, QUEUE_CHECK_TIME

from discord_bot.bot import start_discord_bot  # Import Discord bot



if __name__ == "__main__":
    print(f"{Colors.MAIN} Loading environment...")
    load_dotenv()

    print(f"{Colors.MAIN} Initializing database...")
    init_db()

    # Optional: enqueue a test job
    # enqueue_download("https://www.youtube.com/shorts/K4cxoowc46E")

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        print(f"{Colors.MAIN} Starting background threads...")

        def start_worker():
            try:
                worker_loop(int(QUEUE_CHECK_TIME))
            except Exception as e:
                print(f"{Colors.WORKER} Error: {e}")

        
        threading.Thread(target=start_worker, daemon=True).start()
        if DISCORD_ENABLED:
            threading.Thread(target=start_discord_bot, daemon=True).start()

    print(f"{Colors.MAIN} Starting Flask app...")
    app.run(debug=True, host="0.0.0.0", port=5050)
