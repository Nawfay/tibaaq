
from dotenv import load_dotenv
from groq import Groq
import os

load_dotenv()

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Tandoor
TANDOOR_API_URL = os.getenv("TANDOOR_API_URL")
TANDOOR_API_TOKEN = os.getenv("TANDOOR_API_TOKEN")

# Mealie
MEALIE_API_URL = os.getenv("MEALIE_API_URL")
MEALIE_API_TOKEN = os.getenv("MEALIE_API_TOKEN")

#Instagram
INSTAGRAM_ENABLED = os.getenv("INSTAGRAM_ENABLED")

# Discord
DISCORD_ENABLED = os.getenv("")
DISCORD_TOKEN = os.getenv("")
DISCOED_ALLOWED_USERS = os.getenv("")

client = Groq(api_key=GROQ_API_KEY)
