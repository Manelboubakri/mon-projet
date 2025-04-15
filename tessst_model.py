import os
from groq import Groq

# Définir la clé API
api_key = "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"  # Remplacez par votre clé API

# Définir la clé API dans l'environnement
os.environ["GROQ_API_KEY"] = api_key

# Initialiser le client Groq
client = Groq(api_key=api_key)

def generate_response(prompt):
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

# Tester avec un exemple
prompt = "corrige ce code python : def add(a, b): return a - b"
print("Réponse du modèle :", generate_response(prompt))
