
from dotenv import load_dotenv
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

