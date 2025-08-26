from groq import Groq
import os
import json
import time

from core.external.tandoor import generate_tandoor_prompt
from core.config import client
from core.utils import Colors



def generate_recipe_json(description: str, transcript: str, source_url: str, max_attempts: int = 3) -> dict:
    prompt = generate_tandoor_prompt(description, transcript, source_url)

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"{Colors.GROQ} Attempt {attempt} to generate recipe JSON...")
            response = client.chat.completions.create(
                # model="llama-3.3-70b-versatile", # Works pretty well and gives short-sweet answers (0.5)
                model="openai/gpt-oss-120b", # this is very ChatGPT like , very descriptive (0.15)
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                stream=False,
                temperature=1,
            )

            raw = response.choices[0].message.content.strip()

            # print(f"{Colors.GROQ} Raw JSON: {raw}")
            parsed = json.loads(raw)
            return parsed  # ✅ Valid structured JSON returned

        except json.JSONDecodeError as e:
            print(f"{Colors.GROQ} JSON decode failed: {e}")
        except Exception as e:
            print(f"{Colors.GROQ} Error: {e}")

        if attempt < max_attempts:
            print(f"{Colors.GROQ} Retrying in 1s...")
            time.sleep(1)

    raise RuntimeError("Failed to generate valid recipe JSON after retries.")
