from flask import Flask, request, jsonify
from groq import Groq
from flasgger import Swagger
import os
import subprocess
import re  # Pour extraire uniquement la commande Git

# Définir la clé API Groq
api_key = "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"
os.environ["GROQ_API_KEY"] = api_key

# Initialiser Flask et Swagger
app = Flask(__name__)
swagger = Swagger(app)

# Initialiser Groq Client
client = Groq(api_key=api_key)

@app.route('/execute_git_command', methods=['POST'])
def execute_git_command():
    """
    Génére et exécute une commande Git à partir d'une description naturelle.
    ---
    parameters:
      - name: prompt
        in: body
        required: true
        schema:
          type: object
          properties:
            prompt:
              type: string
              example: "Initialiser un dépôt Git"
    responses:
      200:
        description: Résultat de l'exécution de la commande
        schema:
          type: object
          properties:
            command:
              type: string
              example: "git init"
            output:
              type: string
              example: "Initialized empty Git repository in ..."
      400:
        description: Mauvaise requête
      500:
        description: Erreur interne
    """
    try:
        data = request.get_json()
        prompt = data.get("prompt")

        if not prompt:
            return jsonify({"error": "Le champ 'prompt' est requis"}), 400

        # Générer la commande Git via Groq
        chat_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Réponds uniquement par une commande Git sans explication pour : {prompt}"
            }],
            model="llama3-70b-8192"
        )

        response_text = chat_completion.choices[0].message.content.strip()

        # Extraire la commande Git (ex : "git init")
        match = re.search(r"(git [^\n\r`]*)", response_text)
        if not match:
            return jsonify({
                "raw_response": response_text,
                "error": "Aucune commande Git valide trouvée dans la réponse."
            }), 500

        git_command = match.group(1)

        # Exécuter la commande Git localement
        result = subprocess.run(git_command, shell=True, capture_output=True, text=True)

        return jsonify({
            "command": git_command,
            "output": result.stdout or result.stderr
        })

    except Exception as e:
        return jsonify({"error": f"Erreur du serveur : {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=6970, debug=True)

