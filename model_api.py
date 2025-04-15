# model_api.py

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
api_key = "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"  # ⚠️ Attention à la confidentialité

# Définir la clé API dans l'environnement
os.environ["GROQ_API_KEY"] = api_key

# Créer une instance du client Groq
client = Groq(api_key=api_key)

# ===========================
# 💻 Définir le format des requêtes
# ===========================
class CodeRequest(BaseModel):
    comment: str

# ===========================
# 🚀 Endpoint pour générer du code
# ===========================
@app.post("/generate_code")
def generate_code(request: CodeRequest):
    # Créer la requête au modèle Groq
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": request.comment}
        ],
        model="llama-3.3-70b-versatile",  # Modèle de génération de code
    )

    # Récupérer le code généré
    generated_code = chat_completion.choices[0].message.content.strip()

    return {"generated_code": generated_code}

# ===========================
# 🚀 Lancer le serveur si le script est exécuté directement
# ===========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8111)  # Lancer le serveur sur le port 8000
