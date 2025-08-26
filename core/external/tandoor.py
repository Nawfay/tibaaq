import requests
import os
import json

from core.config import TANDOOR_API_URL, TANDOOR_API_TOKEN
from core.utils import Colors


def push_recipe_to_tandoor(recipe_json: str | dict) -> dict:

    if isinstance(recipe_json, str):
        recipe_json = json.loads(recipe_json)

    headers = {
        "Authorization": f"Bearer {TANDOOR_API_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(f"{TANDOOR_API_URL.rstrip('/')}/recipe/", headers=headers, json=recipe_json)
    print(f"{Colors.TANDOOR} Creating recipe on Tandoor...")

    if response.status_code == 201:
        print(f"{Colors.TANDOOR} Recipe created successfully.")
        return response.json()
    else:
        print(f"{Colors.TANDOOR} Error: {response.status_code} - {response.text}")
        response.raise_for_status()


def upload_tandoor_image(recipe_id: str, image_path: str):

    url = f"{TANDOOR_API_URL.rstrip('/')}/recipe/{recipe_id}/image/"
    headers = {
        "Authorization": f"Bearer {TANDOOR_API_TOKEN}"
    }

    if not os.path.exists(image_path):
        print(f"{Colors.TANDOOR} Image file not found: {image_path}")
        return

    with open(image_path, "rb") as f:
        files = {
            "image": (os.path.basename(image_path), f, "image/jpeg")
        }
        response = requests.put(url, headers=headers, files=files)

    if response.status_code in (200, 201):
        print(f"{Colors.TANDOOR} Thumbnail uploaded successfully to recipe {recipe_id}")
    else:
        print(f"{Colors.TANDOOR} Image upload failed: {response.status_code} - {response.text}")
        response.raise_for_status()


def generate_tandoor_prompt(description: str, transcript: str, source_url: str = "") -> str:
    return f"""
You are a recipe extraction AI.

You are given:
1. A social media **description** — usually includes a list of ingredients
2. A **transcription** — the spoken instructions from a cooking video

Your job is to generate a valid JSON recipe compatible with the **Tandoor recipe API**.

---

### REQUIRED JSON STRUCTURE

- `name`: Recipe title (string)
- `description`: Short summary of the dish (string)
- `keywords`: List of dicts like: [{{"name": "...", "description": "..."}}]
- `steps`: A list of cooking steps. Each must include:
  - `name`: Step title (string)
  - `instruction`: Full instruction text (string)
  - `order`: Step number (integer)
  - `time`: Time in minutes (integer)
  - `ingredients`: Must be a list of complete ingredients. Every ingredient **must** contain:
    - `food`: {{ "name": "onion" }}
    - `unit`: {{ "name": "gram" }} — **this must NOT be missing or blank**
    - `amount`: a number (e.g. `100`, `0.5`) — **must NOT be a string**

- `servings`: Number of servings (integer)
- `working_time`: Total **active** cooking/prep time in minutes (integer)
- `waiting_time`: Total **passive/wait** time (marination, resting, baking, etc) in minutes
- `source_url`: Must be set to: {source_url}
- `internal`: false
- `show_ingredient_overview`: true

---

### UNIT RULES (IMPORTANT)

- ✅ Use realistic cooking units like: `"gram"`, `"ml"`, `"teaspoon"`, `"tablespoon"`, `"cup"`, `"clove"`, `"slice"`, `"can"`
- ✅ Only use `"piece"` for things like eggs, onions, or lemons — never for powders, oils, or spices
- ❌ NEVER use `"piece"` for salt, sugar, flour, oil, spices — instead use `"teaspoon"`, `"tablespoon"`, or `"gram"`
- ❌ Avoid `"pinch"` unless it is clearly said, and never for liquids
- ✅ If you're unsure, **guess something logical** like `"teaspoon"` for salt, `"tablespoon"` for oil, `"cup"` for flour, etc.
- ❌ Do NOT include blank, null, or empty units

---

### VALIDATION RULES

- ✅ Every ingredient must have a `unit.name` and numeric `amount`. Never skip these.
- ❌ Do **not** include empty ingredient objects (`{{}}`)
- ❌ Do not use strings for numbers like `"1/2"` — convert to `0.5`
- ❌ Do not use nulls, empty strings, or missing fields
- ✅ If you can't find an amount, guess a realistic default (e.g., `1` or `0.5`)

---

# DESCRIPTION:
{description}

# TRANSCRIPTION:
{transcript}
"""

