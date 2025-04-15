from fastapi import FastAPI
from pydantic import BaseModel
import os
from groq import Groq

# Créer l'application FastAPI
app = FastAPI()

# ===========================
# 🔧 Configurer la clé API et client Groq
# ===========================
# Définir ta clé API (Assurez-vous que cette clé est bien protégée)
api_key = "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"  # ⚠️ Remplacez avec votre propre clé API Groq

# Définir la clé API dans l'environnement
os.environ["GROQ_API_KEY"] = api_key

# Créer une instance du client Groq
client = Groq(api_key=api_key)

# ===========================
# 💻 Définir le format des requêtes
# ===========================
class CodeRequest(BaseModel):
    code: str  # Le code Python pour lequel générer des tests unitaires

# ===========================
# 🚀 Endpoint pour générer des tests unitaires
# ===========================
@app.post("/generate_tests")
def generate_tests(request: CodeRequest):
    # Créer la requête au modèle Groq pour générer des tests unitaires
    chat_completion = client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": f"Voici un code Python :\n{request.code}\nGénère des tests unitaires pour ce code."
        }],
        model="llama-3.3-70b-versatile",  # Modèle utilisé pour générer des tests unitaires
    )

    # Récupérer les tests unitaires générés
    generated_tests = chat_completion.choices[0].message.content.strip()

    return {"generated_tests": generated_tests}

# ===========================
# 🚀 Lancer le serveur si le script est exécuté directement
# ===========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Lancer le serveur sur le port 8005
