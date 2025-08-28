import os
import re
import time
import random
import threading
from datetime import datetime, date
from instagrapi import Client
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# from core.queue.queue import enqueue_download

# Config
USERNAME = "tibaa.q"
PASSWORD = "Dishit79@123"
SETTINGS_FILE = "insta/insta_settings.json"
POLL_INTERVAL_MINUTES = 180  # Increased from 90 to 180 minutes
WATCHER = "\033[95m[Watcher]\033[0m"
REEL_REGEX = r"https?://www\.instagram\.com/reel/[A-Za-z0-9_-]+/?"

# API call tracking
api_calls = {
    "today": date.today(),
    "count": 0,
    "limit": 200  # Set a reasonable daily limit
}

# Hardcoded user IDs
TARGET_USERS = {
    "dis.hit": 8155993982,
    # Add more if needed
    # "chef.bano": 1234567890
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

def track_api_call():
    """Track API calls and check if we're over limit"""
    today = date.today()
    
    # Reset counter if it's a new day
    if api_calls["today"] != today:
        api_calls["today"] = today
        api_calls["count"] = 0
    
    api_calls["count"] += 1
    
    # Check if we're over limit
    if api_calls["count"] >= api_calls["limit"]:
        print(f"{WATCHER} ⛔ DAILY LIMIT REACHED ({api_calls['count']}). Stopping until tomorrow.")
        return False
    
    if api_calls["count"] % 10 == 0:
        print(f"{WATCHER} API call count: {api_calls['count']}/{api_calls['limit']}")
    
    return True

def is_rate_limit_error(error_message):
    """Check if an error is related to rate limiting"""
    rate_limit_keywords = [
        "rate limit", "too many requests", "429", "wait", 
        "try again later", "temporarily blocked", "feedback_required"
    ]
    error_str = str(error_message).lower()
    return any(keyword in error_str for keyword in rate_limit_keywords)

def init_instagram(force_new_session=False):
    """Initialize Instagram client with session management"""
    if os.path.exists(SETTINGS_FILE) and not force_new_session:
        cl.load_settings(SETTINGS_FILE)
        try:
            if not track_api_call():
                return False
            cl.get_timeline_feed()
            print(f"{WATCHER} Session restored.")
            return True
        except Exception as e:
            print(f"{WATCHER} Session expired or error: {e}")
            # Fall through to re-login
    
    try:
        print(f"{WATCHER} {'Creating new' if force_new_session else 'Logging in to'} session...")
        cl.login(USERNAME, PASSWORD)
        cl.dump_settings(SETTINGS_FILE)
        print(f"{WATCHER} Login successful.")
        return True
    except Exception as e:
        print(f"{WATCHER} ❌ Login failed: {e}")
        return False

def extract_reel_from_message(msg):
    """Extract reel URLs from a message"""
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
    """Check if a reel has already been processed"""
    return session.query(Reel).filter_by(url=url).first() is not None

def store_reel(session, url, sender):
    """Store a reel in the database"""
    session.add(Reel(url=url, sender=sender))
    session.commit()

def safe_direct_messages(thread_id, retries=5):
    """Safely get direct messages with retry logic and rate limit handling"""
    if not track_api_call():
        return []  # Stop if over daily limit
        
    for attempt in range(retries):
        try:
            return cl.direct_messages(thread_id, amount=20)
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a rate limit error
            if is_rate_limit_error(error_str):
                # Much longer backoff for rate limits
                wait = 60 * (3 ** attempt)  # 1min, 3min, 9min, 27min, 81min
                print(f"{WATCHER} 🚫 RATE LIMITED. Backing off for {wait/60:.1f} minutes: {e}")
            else:
                # Regular error, shorter backoff
                base_wait = 10 * (2 ** attempt)
                wait = random.uniform(base_wait, base_wait * 3)
                print(f"{WATCHER} ⚠️ Error (retry {attempt+1}/{retries}): {e}")
                
            time.sleep(wait)
    
    print(f"{WATCHER} ❌ Failed to get messages after {retries} attempts")
    return []

def safe_direct_threads(amount=5, retries=5):
    """Safely get direct threads with retry logic"""
    if not track_api_call():
        return []  # Stop if over daily limit
        
    for attempt in range(retries):
        try:
            return cl.direct_threads(amount=amount)
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a rate limit error
            if is_rate_limit_error(error_str):
                # Much longer backoff for rate limits
                wait = 60 * (3 ** attempt)  # 1min, 3min, 9min, 27min, 81min
                print(f"{WATCHER} 🚫 RATE LIMITED. Backing off for {wait/60:.1f} minutes: {e}")
            else:
                # Regular error, shorter backoff
                base_wait = 10 * (2 ** attempt)
                wait = random.uniform(base_wait, base_wait * 3)
                print(f"{WATCHER} ⚠️ Error (retry {attempt+1}/{retries}): {e}")
                
            time.sleep(wait)
    
    print(f"{WATCHER} ❌ Failed to get threads after {retries} attempts")
    return []

def run_watcher():
    """Main watcher loop with improved error handling"""
    consecutive_errors = 0
    max_consecutive_errors = 3
    
    while True:
        try:
            # Initialize Instagram with a new session if we had errors
            if not init_instagram(force_new_session=(consecutive_errors > 0)):
                # If initialization failed, wait and try again
                wait_time = 60 * 60  # 1 hour
                print(f"{WATCHER} Failed to initialize. Waiting {wait_time/60} minutes...")
                time.sleep(wait_time)
                continue

            # Preload threads
            all_threads = safe_direct_threads(amount=5)
            if not all_threads:
                raise Exception("Failed to load threads")
                
            user_threads = {}

            for username, user_id in TARGET_USERS.items():
                thread = next((t for t in all_threads if user_id in [u.pk for u in t.users]), None)
                if thread:
                    user_threads[username] = thread
                    print(f"{WATCHER} Watching {username} (ID: {user_id})")
                else:
                    print(f"{WATCHER} ❌ No thread found for {username} ({user_id})")

            if not user_threads:
                print(f"{WATCHER} ❌ No valid threads. Waiting before retry...")
                time.sleep(60 * 30)  # 30 minutes
                continue

            print(f"{WATCHER} Ready. Polling every ~{POLL_INTERVAL_MINUTES} minutes...\n")

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

                    # Add a longer delay between users to avoid rate limits
                    time.sleep(random.uniform(5, 10))
                except Exception as e:
                    print(f"{WATCHER} ❌ Error with {username}: {e}")

            session.close()
            print(f"{WATCHER} ✅ Cycle complete: {datetime.utcnow().isoformat()} UTC\n")
            
            # If we get here without errors, reset the counter
            consecutive_errors = 0
            
            # Add jitter to polling interval
            jitter = random.uniform(0.8, 1.2)  # ±20% jitter
            sleep_time = POLL_INTERVAL_MINUTES * 60 * jitter
            print(f"{WATCHER} Sleeping for ~{sleep_time/60:.1f} minutes...\n")
            time.sleep(sleep_time)
            
        except Exception as e:
            consecutive_errors += 1
            print(f"{WATCHER} 🔴 Major error: {e}")
            
            if consecutive_errors >= max_consecutive_errors:
                cooldown = 60 * 60 * 4  # 4 hours
                print(f"{WATCHER} ⛔ Too many consecutive errors. Cooling down for {cooldown/60/60} hours")
                time.sleep(cooldown)
                consecutive_errors = 0
            else:
                wait = 60 * 15 * consecutive_errors  # 15, 30, 45 minutes
                print(f"{WATCHER} Backing off for {wait/60} minutes before retry")
                time.sleep(wait)

def start_reel_watcher():
    """Start the watcher in a background thread"""
    t = threading.Thread(target=run_watcher, daemon=True)
    t.start()
    print(f"{WATCHER} Background thread started")