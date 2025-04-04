import os
from flask import Flask, request, jsonify
from flasgger import Swagger  # Pour Swagger
from groq import Groq
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import subprocess

# Initialisation de Flask
app = Flask(__name__)

# Initialisation de Swagger pour la documentation API
swagger = Swagger(app)

# Définition de la clé API pour Groq
api_key = "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"
os.environ["GROQ_API_KEY"] = api_key

# Initialisation du client Groq
groq_client = Groq(api_key=api_key)

# Chargement du modèle de génération de code
model_path = r"C:\Users\USER\Downloads\codegen_project\codegen_model"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

# Forcer l'utilisation du CPU
device = torch.device("cpu")
model.to(device)

# ✅ Fonction pour la correction de code via Groq
def correct_code(prompt: str) -> str:
    """
    Envoie un prompt à l'API Groq pour correction de code.
    """
    chat_completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="deepseek-r1-distill-qwen-32b",
    )
    return chat_completion.choices[0].message.content

# ✅ Fonction pour la génération de code via Transformers
def generate_code(comment: str) -> str:
    """
    Génère du code à partir d'un commentaire avec le modèle Transformers.
    """
    inputs = tokenizer(comment, return_tensors="pt").to(device)
    outputs = model.generate(**inputs, max_length=150)
    code = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return code

# ✅ Fonction pour exécuter une commande Git en toute sécurité
def execute_git_command(command: str) -> str:
    """
    Exécute une commande Git et retourne la sortie, avec des restrictions pour éviter les commandes dangereuses.
    """
    # Liste des commandes interdites
    forbidden_commands = ["reset --hard", "rm -rf", "rebase", "checkout -f"]

    # Vérification de sécurité
    for forbidden in forbidden_commands:
        if forbidden in command:
            return f"❌ ERREUR : La commande '{command}' est interdite pour des raisons de sécurité."

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            return f"❌ Erreur lors de l'exécution de la commande : {result.stderr.strip()}"
        return result.stdout.strip()
    except Exception as e:
        return f"❌ Erreur système : {str(e)}"

# ✅ Orchestrateur pour choisir la bonne fonction en fonction de la demande
def orchestrate_request(request_data: dict) -> str:
    """
    Analyse la demande et redirige vers la fonction appropriée.
    """
    prompt = request_data.get("prompt", "").strip()

    if not prompt:
        raise ValueError("⚠️ Le champ 'prompt' est requis.")

    if "corrige" in prompt.lower():  # Correction de code
        return correct_code(prompt)
    elif prompt.lower().startswith("git "):  # Commande Git
        return execute_git_command(prompt)
    else:  # Génération de code
        return generate_code(prompt)

# ✅ Route Flask pour traiter les requêtes API
@app.route('/predict', methods=['POST'])
def predict():
    """
    Endpoint API pour traiter les requêtes de correction, génération ou exécution de Git.
    ---
    parameters:
      - name: prompt
        in: body
        type: string
        required: true
        description: Texte décrivant la demande (corriger, générer du code ou exécuter une commande Git).
    responses:
      200:
        description: Réponse du modèle après traitement.
        schema:
          type: object
          properties:
            response:
              type: string
              example: "Voici la correction du code : def add(a, b): return a + b"
      400:
        description: Mauvaise requête, le champ 'prompt' est requis.
        schema:
          type: object
          properties:
            error:
              type: string
              example: "⚠️ Le champ 'prompt' est requis."
      500:
        description: Erreur interne du serveur.
        schema:
          type: object
          properties:
            error:
              type: string
              example: "❌ Erreur du serveur."
    """
    try:
        data = request.get_json()
        response = orchestrate_request(data)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Lancement de l'API Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007, debug=True)

