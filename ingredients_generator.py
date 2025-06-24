from mistralai import UserMessage, SystemMessage
import json
from kitchen_data import get_utensils_by_type
import re

def generate_ingredients(client, model_name, recipe_title, ingredients, utensil_type="traditional"):
    ingredients_str = "\n".join(f"- {item['quantity']} {item['name']}" for item in ingredients)
    utensils = get_utensils_by_type(utensil_type)
    utensils_text = ", ".join(utensils)

    prompt = f"""
You are a French cooking assistant.

Generate the list of ingredients (with quantities) for the recipe titled "{recipe_title}".
The user has the following ingredients:
{ingredients_str}

The available utensils are:
{utensils_text}

⚠️ Use ONLY the ingredients listed above. Do not add any extra ingredients.

Return the result in JSON format like this:

{{
  "title": "{recipe_title}",
  "ingredients": ["item1", "item2", "..."]
}}
"""

    messages = [
        SystemMessage(content="You generate JSON outputs for ingredients."),
        UserMessage(content=prompt.strip())
    ]

    response = client.chat.complete(model=model_name, messages=messages, temperature=1.0)
    content = response.choices[0].message.content.strip()

    # 🔍 Nettoyage du JSON si entouré de ```json ... ```
    content = re.sub(r"^```json|```$", "", content).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format from model", "raw": content}
