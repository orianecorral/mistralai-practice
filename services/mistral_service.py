import os
import json
import re
from dotenv import load_dotenv
from mistralai import Mistral
from mistralai import UserMessage, SystemMessage

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)
model_name = "mistral-medium-latest"


def ask_mistral(message: str, context: str = "") -> str:
    """
    Envoie un prompt simple à Mistral et retourne la réponse en texte brut.
    """
    prompt = f"{context.strip()}\n{message.strip()}"
    messages = [
        SystemMessage(content="Tu es un assistant culinaire."),
        UserMessage(content=prompt)
    ]

    response = client.chat.complete(
        model=model_name,
        messages=messages,
        temperature=1.0
    )
    return response.choices[0].message.content.strip()


def ask_mistral_json(message: str, context: str = "") -> dict:
    """
    Envoie un prompt à Mistral et tente de parser la réponse en JSON.
    """
    prompt = f"{context.strip()}\n{message.strip()}"
    messages = [
        SystemMessage(content="Tu es un assistant culinaire. Tu dois répondre avec un JSON valide."),
        UserMessage(content=prompt)
    ]

    response = client.chat.complete(
        model=model_name,
        messages=messages,
        temperature=1.0
    )

    content = response.choices[0].message.content.strip()

    # Nettoyage si la réponse est entourée de balises de code
    content = re.sub(r"^```json\s*|```$", "", content).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("🧠 Réponse non parsable :", content)
        return {"error": "Invalid JSON format", "raw": content}
