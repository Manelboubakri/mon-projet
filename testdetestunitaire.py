# Installer la bibliothèque groq si ce n'est pas déjà fait
# !pip install groq  # À exécuter dans le terminal si nécessaire

# Importation des bibliothèques nécessaires
import os
from groq import Groq

# Définir la clé API Groq
api_key = "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"  # Votre clé API Groq

# Définir la clé API dans l'environnement
os.environ["GROQ_API_KEY"] = api_key

# Créer une instance du client Groq avec la clé API
client = Groq(api_key=api_key)

# Code Python pour lequel vous voulez générer des tests unitaires
code_to_test = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""

# Demander au modèle de générer des tests unitaires pour le code Python fourni
chat_completion = client.chat.completions.create(
    messages=[{
        "role": "user",
        "content": f"Voici un code Python :\n{code_to_test}\nGénère des tests unitaires pour ce code."
    }],
    model="llama-3.3-70b-versatile",  # Modèle utilisé pour générer des tests unitaires
)

# Affichage des tests unitaires générés par le modèle
print(chat_completion.choices[0].message.content)
