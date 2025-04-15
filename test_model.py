
# Importer les bibliothèques nécessaires
import os
from groq import Groq

# Définir ta clé API
api_key = "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"  # ⚠️ Attention à la confidentialité

# Définir la clé API dans l'environnement
os.environ["GROQ_API_KEY"] = api_key

# Créer une instance du client
client = Groq(api_key=api_key)

# === Ton commentaire (description de la tâche à faire) ===
description = "Écris une fonction Python qui trie une liste de nombres en ordre croissant en utilisant le tri par insertion."

# Créer la requête au modèle
chat_completion = client.chat.completions.create(
    messages=[
        {"role": "user", "content": description}
    ],
    model="llama-3.3-70b-versatile",  # ou deepseek-coder:6.7b pour génération de code
)

# Afficher le code généré
print("💡 Code généré à partir du commentaire :\n")
print(chat_completion.choices[0].message.content)

