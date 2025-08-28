import os
import re
import time
import random
import threading
from datetime import datetime
from instagrapi import Client
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# from core.queue.queue import enqueue_download

# Config
SETTINGS_FILE = "insta/insta_settings.json"
POLL_INTERVAL_MINUTES = 90
WATCHER = "\033[95m[Watcher]\033[0m"
REEL_REGEX = r"https?://www\.instagram\.com/reel/[A-Za-z0-9_-]+/?"

# Hardcoded user IDs
TARGET_USERS = {
    "dis.hit": 8155993982,
    # Add more if needed
}

# SQLAlchemy
Base = declarative_base()
engine = create_engine("sqlite:///seen_reels.db")
Session = sessionmaker(bind=engine)

class Reel(Base):
    __tablename__ = "reels"
    url = Column(String, primary_key=True)
    sender = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# Instagram client
cl = Client()

def init_instagram():
    if os.path.exists(SETTINGS_FILE):
        cl.load_settings(SETTINGS_FILE)
        try:
            cl.get_timeline_feed()
            print(f"{WATCHER} Session restored.")
        except Exception:
            print(f"{WATCHER} Session expired. Logging in...")
            cl.login(USERNAME, PASSWORD)
            cl.dump_settings(SETTINGS_FILE)
    else:
        cl.login(USERNAME, PASSWORD)
        cl.dump_settings(SETTINGS_FILE)

def extract_reel_from_message(msg):
    urls = []

    if msg.text:
        urls.extend(re.findall(REEL_REGEX, msg.text))

    if hasattr(msg, "reel_share") and msg.reel_share and msg.reel_share.media:
        urls.append(f"https://www.instagram.com/reel/{msg.reel_share.media.code}/")

    if hasattr(msg, "clip") and msg.clip:
        urls.append(f"https://www.instagram.com/reel/{msg.clip.code}/")

    if hasattr(msg, "media_share") and msg.media_share and getattr(msg.media_share, "media_type", None) == 2:
        urls.append(f"https://www.instagram.com/reel/{msg.media_share.code}/")

    return urls

def reel_already_seen(session, url):
    return session.query(Reel).filter_by(url=url).first() is not None

def store_reel(session, url, sender):
    session.add(Reel(url=url, sender=sender))
    session.commit()

def safe_direct_messages(thread_id, retries=3):
    for attempt in range(retries):
        try:
            return cl.direct_messages(thread_id, amount=20)
        except Exception as e:
            wait = random.uniform(3, 6) * (attempt + 1)
            print(f"{WATCHER} ⚠️ Retry ({attempt+1}) on error: {e}")
            time.sleep(wait)
    return []

def run_watcher():
    init_instagram()

    # Preload threads
    all_threads = cl.direct_threads(amount=5)
    user_threads = {}

    for username, user_id in TARGET_USERS.items():
        thread = next((t for t in all_threads if user_id in [u.pk for u in t.users]), None)
        if thread:
            user_threads[username] = thread
            print(f"{WATCHER} Watching {username} (ID: {user_id})")
        else:
            print(f"{WATCHER} ❌ No thread found for {username} ({user_id})")

    if not user_threads:
        print(f"{WATCHER} ❌ No valid threads. Exiting.")
        return

    print(f"{WATCHER} Ready. Polling every {POLL_INTERVAL_MINUTES} minutes...\n")

    while True:
        session = Session()

        for username, thread in user_threads.items():
            try:
                messages = safe_direct_messages(thread.id)

                for msg in messages:
                    sender = "You" if msg.user_id == cl.user_id else username
                    reel_urls = extract_reel_from_message(msg)

                    for url in reel_urls:
                        if not reel_already_seen(session, url):
                            print(f"{WATCHER} [NEW] {sender}: {url}")
                            store_reel(session, url, sender)
                            # enqueue_download(url)
                        else:
                            print(f"{WATCHER} [✓] Seen: {url}")

                time.sleep(random.uniform(1, 3))  # 🕓 small delay between users
            except Exception as e:
                print(f"{WATCHER} ❌ Error with {username}: {e}")

        session.close()
        print(f"{WATCHER} ✅ Cycle complete: {datetime.utcnow().isoformat()} UTC\n")
        print(f"{WATCHER} Sleeping for {POLL_INTERVAL_MINUTES} minutes...\n")
        time.sleep(POLL_INTERVAL_MINUTES * 60)

def start_reel_watcher():
    t = threading.Thread(target=run_watcher, daemon=True)
    t.start()
