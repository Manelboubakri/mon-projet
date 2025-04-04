
import os
from groq import Groq

# 🔑 Définir ta clé API Groq (REMPLACE PAR TA CLÉ)
api_key = "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"  # ⚠️ Remplace ceci avec ta clé API Groq

# Stocker la clé API dans l'environnement (optionnel)
os.environ["GROQ_API_KEY"] = api_key

# Initialiser le client Groq
client = Groq(api_key=api_key)

def generate_git_command(request):
    """
    Génère une commande Git en fonction d'une requête utilisateur.

    Paramètre:
    - request (str): Description de l'action Git souhaitée.

    Retourne:
    - str: Commande Git générée par le modèle.
    """
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": f"Génère une commande Git pour : {request}"}],
        model="llama-3.3-70b-versatile"
    )

    return chat_completion.choices[0].message.content

# ✅ TESTS : Générer des commandes Git
if __name__ == "__main__":
    tests = [
        "Cloner un dépôt GitHub",
        "Créer un nouveau dépôt Git et faire un premier commit",
        "Mettre à jour la branche principale avec la dernière version du dépôt distant",
        "Annuler le dernier commit tout en conservant les modifications",
        "Créer une nouvelle branche et basculer dessus",
        "Ajouter et pousser un fichier nommé 'main.py' dans le dépôt distant"
    ]

    for test in tests:
        print(f"🛠️ Requête : {test}")
        print(f"📌 Commande Git : {generate_git_command(test)}\n")
