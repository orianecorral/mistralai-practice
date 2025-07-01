from fastapi import APIRouter
from models.schemas import Prompt
from services.mistral_service import ask_mistral

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.post("/titles")
def generate_titles(prompt: Prompt):
    return {"titles": ask_mistral(prompt.message, "Génère 5 titres de recettes")}

@router.post("/ingredients")
def generate_ingredients(prompt: Prompt):
    return {"ingredients": ask_mistral(prompt.message, "Liste les ingrédients nécessaires")}

@router.post("/steps")
def generate_steps(prompt: Prompt):
    return {"steps": ask_mistral(prompt.message, "Décris les étapes de préparation")}
