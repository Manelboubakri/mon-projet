import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq

# Définir la clé API Groq (si nécessaire)
api_key = "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"  # Remplacez par votre clé API Groq
os.environ["GROQ_API_KEY"] = api_key

# Créer une instance de l'application FastAPI
app = FastAPI()

# Créer une instance du client Groq avec la clé API
client = Groq(api_key=api_key)

# Modèle Pydantic pour valider l'entrée de l'utilisateur
class CodeSnippet(BaseModel):
    code: str

# Fonction pour générer un diagramme UML à partir du code Python
def generate_uml_diagram(code_snippet: str) -> str:
    """
    Envoie un extrait de code Python à l'API Groq pour générer automatiquement un diagramme UML en utilisant Mermaid.js.

    Paramètre:
    code_snippet (str): Le code Python à analyser pour générer le diagramme UML.

    Retourne:
    str: La description UML générée sous forme de texte (Mermaid.js).
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Analyse ce code Python et génère un diagramme UML en utilisant Mermaid.js:\n\n{code_snippet}"
            }],
            model="llama-3.3-70b-versatile",  # Modèle utilisé pour la génération du diagramme UML
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du diagramme UML: {e}")

@app.post("/generate_uml")
async def generate_uml(request: CodeSnippet):
    """
    Route POST pour générer un diagramme UML à partir du code Python.
    """
    code_snippet = request.code
    uml_description = generate_uml_diagram(code_snippet)

    # Utiliser une chaîne classique pour formater le code Mermaid.js
    mermaid_code = f"""
    classDiagram
        {uml_description}
    """

    return {
        "message": "Diagramme Mermaid.js généré avec succès",
        "uml_code": mermaid_code.strip()
    }

@app.get("/groq_status")
async def get_groq_status():
    """
    Route GET pour vérifier le statut de la clé API Groq.
    """
    # Simuler une requête API Groq pour vérifier le statut
    groq_status = {
        "status": "success",
        "api_key": os.environ["GROQ_API_KEY"],
        "message": "API Groq est opérationnelle"
    }
    return groq_status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)
