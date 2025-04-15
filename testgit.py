import os
import subprocess
from groq import Groq

# 🔑 Définir ta clé API Groq
api_key = "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"  # ⚠️ Remplace cette clé par la tienne

# Initialiser le client Groq
client = Groq(api_key=api_key)

def generate_git_command(request):
    """
    Génère une commande Git en fonction d'une requête utilisateur.
    """
    prompt = (
        "Contexte : Tu es un expert Git. Donne uniquement la commande Git exacte à exécuter pour accomplir la tâche suivante, sans explication ni commentaire.\n"
        f"Tâche : {request}"
    )

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )

    return chat_completion.choices[0].message.content.strip()

def execute_git_command(command):
    """
    Exécute une commande shell (ex : git init) et retourne la sortie ou l'erreur.
    """
    try:
        print(f"📦 Exécution de la commande : {command}")
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("✅ Résultat :")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ Erreur lors de l'exécution :")
        print(e.stderr)

if __name__ == "__main__":
    while True:
        user_input = input("\n📝 Que veux-tu faire avec Git ? (ou 'exit' pour quitter) : ")
        if user_input.lower() == "exit":
            break
        command = generate_git_command(user_input)
        execute_git_command(command)
