# Importation des bibliothèques nécessaires
import os
from groq import Groq

# Définir la clé API Groq
api_key = "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"  # Remplacez par votre clé API Groq

# Définir la clé API dans l'environnement
os.environ["GROQ_API_KEY"] = api_key

# Créer une instance du client Groq avec la clé API
client = Groq(api_key=api_key)

# Fonction pour générer la documentation automatique d'un code Python
def generate_documentation(code_snippet):
    """
    Envoie un extrait de code Python à l'API Groq pour générer automatiquement une documentation détaillée.

    Paramètre:
    code_snippet (str): Le code Python à documenter.

    Retourne:
    str: La documentation générée.
    """
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Ajoute une documentation automatique à ce code en ajoutant des docstrings et des commentaires :\n\n{code_snippet}"
            }
        ],
        model="llama-3.3-70b-versatile",  # Modèle utilisé pour la génération de documentation
    )

    return chat_completion.choices[0].message.content

# Exemple de code Python à documenter
code_example = """
def multiply(x, y):
    return x * y
"""

# Génération de la documentation
documentation = generate_documentation(code_example)

# Affichage de la documentation générée
print(documentation)