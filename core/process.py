from groq import Groq
import os
import json
import time

from core.external.tandoor import generate_tandoor_prompt
from core.config import client



def generate_recipe_json(description: str, transcript: str, source_url: str, max_attempts: int = 3) -> dict:
    prompt = generate_tandoor_prompt(description, transcript, source_url)

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"[Groq] Attempt {attempt} to generate recipe JSON...")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                # max_completion_tokens=1024,
                response_format={"type": "json_object"},
                stream=False,
                temperature=1,
            )

            raw = response.choices[0].message.content.strip()

            # print(f"[Groq] Raw JSON: {raw}")
            parsed = json.loads(raw)
            return parsed  # ✅ Valid structured JSON returned

        except json.JSONDecodeError as e:
            print(f"[Groq] JSON decode failed: {e}")
        except Exception as e:
            print(f"[Groq] Error: {e}")

        if attempt < max_attempts:
            print("[Groq] Retrying in 1s...")
            time.sleep(1)

    raise RuntimeError("Failed to generate valid recipe JSON after retries.")
