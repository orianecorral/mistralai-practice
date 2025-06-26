import json
import re
import datetime
import sqlite3
from pathlib import Path
from title_generator import generate_titles_json
from ingredients_generator import generate_ingredients
from steps_generator import generate_steps
from utils import load_api_key
from mistralai import Mistral

DB_PATH = "recettes.db"

def slugify(text):
    return re.sub(r'\W+', '_', text.strip().lower())

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            ingredients_input TEXT,
            generated_ingredients TEXT,
            steps TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_recipe_to_db(recipe):
    print("💾 Insertion dans la DB en cours...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO recipes (title, ingredients_input, generated_ingredients, steps, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        recipe["title"],
        json.dumps(recipe["ingredients_input"], ensure_ascii=False),
        json.dumps(recipe["generated_ingredients"], ensure_ascii=False),
        json.dumps(recipe["steps"], ensure_ascii=False),
        datetime.datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    print(f"🗄️ Recette sauvegardée dans la base SQLite : {DB_PATH}")

def main():
    init_db()
    api_key = load_api_key()
    client = Mistral(api_key=api_key)
    model_name = "mistral-medium-latest"

    raw_ingredients = input("Entrez vos ingrédients avec quantité (ex: 3 carottes, 200g jambon) : ").split(",")
    ingredients_input = [i.strip() for i in raw_ingredients if i.strip()]
    dietary_pref = input("Préférence alimentaire (optionnel) : ").strip()
    utensils_type = input("Type d’ustensiles disponibles (traditional / modern) : ").strip().lower()

    utensils = []
    if utensils_type == "traditional":
        utensils = [
            "wooden spoon", "frying pan", "saucepan", "knife", "cutting board", "whisk", "colander"
        ]
    elif utensils_type == "modern":
        utensils = [
            "Thermomix", "air fryer", "pressure cooker", "food processor", "blender", "induction hob"
        ]

    print("\n🔎 Recherche de recettes avec les seuls ingrédients donnés...")
    response = generate_titles_json(client, model_name, ingredients_input, dietary_pref, utensils)
    titles = response.get("titles", [])

    if not titles:
        print("\n⚠️ Aucun titre de recette n’a pu être généré uniquement avec les ingrédients fournis.")
        add_more = input("Souhaitez-vous ajouter des ingrédients supplémentaires ? (oui/non) : ").strip().lower()
        if add_more == "oui":
            new_ingredients = input("Entrez les nouveaux ingrédients avec quantités (ex: 1 oignon, 2 œufs) : ").split(",")
            ingredients_input += [i.strip() for i in new_ingredients if i.strip()]
            response = generate_titles_json(client, model_name, ingredients_input, dietary_pref, utensils)
            titles = response.get("titles", [])
            if not titles:
                print(json.dumps({"error": "Aucune recette trouvée même avec des ingrédients supplémentaires."}))
                return
        else:
            print(json.dumps({"error": "Aucune recette trouvée."}))
            return

    print("\n🍽️ Recettes proposées :")
    for idx, title in enumerate(titles, 1):
        print(f"{idx}. {title}")

    try:
        choice = int(input("\nChoisissez une recette (numéro) : ")) - 1
        chosen_title = titles[choice]
    except (ValueError, IndexError):
        print(json.dumps({"error": "Choix invalide."}))
        return

    parsed_ingredients = []
    for item in ingredients_input:
        parts = item.split(maxsplit=1)
        if len(parts) == 2:
            parsed_ingredients.append({"quantity": parts[0], "name": parts[1]})
        else:
            parsed_ingredients.append({"quantity": "1", "name": parts[0]})

    ingredients_list = generate_ingredients(client, model_name, chosen_title, parsed_ingredients, utensils_type)
    steps = generate_steps(client, model_name, chosen_title, parsed_ingredients, utensils_type)

    print("\n✅ Recette choisie :", chosen_title)
    print("\n🧂 Ingrédients générés :")
    for item in ingredients_list:
        print(f"- {item}")
    print("\n👨‍🍳 Étapes de la recette :")
    for idx, step in enumerate(steps, 1):
        print(f"{idx}. {step}")

    result = {
        "title": chosen_title,
        "ingredients_input": parsed_ingredients,
        "generated_ingredients": ingredients_list,
        "steps": steps
    }

    print("\n📤 JSON complet à utiliser dans le front :")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 💾 Sauvegarde dans un fichier individuel
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = slugify(chosen_title)
    output_filename = f"recette_{safe_title}_{date_str}.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Résultat sauvegardé dans le fichier : {output_filename}")

    # 🗄️ Sauvegarde dans SQLite
    save_recipe_to_db(result)

    # ✅ Vérification du contenu de la base
    print("\n📚 Contenu actuel de la base :")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, created_at FROM recipes ORDER BY id DESC")
    for row in cursor.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    main()
