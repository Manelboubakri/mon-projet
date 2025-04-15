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
    code: str  # Le code Python pour lequel générer la documentation

# ===========================
# 🚀 Endpoint pour générer la documentation
# ===========================
@app.post("/generate_documentation")
def generate_documentation(request: CodeRequest):
    # Créer la requête au modèle Groq pour générer la documentation
    chat_completion = client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": f"Voici un code Python :\n{request.code}\nGénère de la documentation pour ce code en ajoutant des docstrings et des commentaires."
        }],
        model="llama-3.3-70b-versatile",  # Modèle utilisé pour générer la documentation
    )

    # Récupérer la documentation générée
    generated_documentation = chat_completion.choices[0].message.content.strip()

    return {"generated_documentation": generated_documentation}

# ===========================
# 🚀 Lancer le serveur si le script est exécuté directement
# ===========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9400)  # Lancer le serveur sur le port 8000
