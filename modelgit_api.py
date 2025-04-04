from flask import Flask, request, jsonify
from groq import Groq
import os
from flasgger import Swagger

# Initialiser Flask
app = Flask(__name__)

# Initialiser Swagger pour la documentation de l'API
swagger = Swagger(app)

# Définir la clé API Groq
api_key = "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"  # Remplacez par votre clé API Groq
os.environ["GROQ_API_KEY"] = api_key

# Créer un client Groq
client = Groq(api_key=api_key)

@app.route('/generate_git_command', methods=['POST'])
def generate_git_command():
    """
    Cette fonction prend une requête utilisateur et génère une commande Git à l'aide du modèle Groq.
    ---
    parameters:
      - name: prompt
        in: body
        type: string
        required: true
        description: La description de l'action Git à générer (par exemple, "Cloner un dépôt GitHub")
    responses:
      200:
        description: La commande Git générée par le modèle Groq
        schema:
          type: object
          properties:
            response:
              type: string
              example: "git clone https://github.com/username/repository.git"
      400:
        description: Mauvaise requête, le champ 'prompt' est requis
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Le champ 'prompt' est requis"
      500:
        description: Erreur interne du serveur
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Erreur du serveur"
    """
    try:
        # Récupérer les données JSON envoyées par le client
        data = request.get_json()
        user_prompt = data.get("prompt", "")

        if not user_prompt:
            return jsonify({"error": "Le champ 'prompt' est requis"}), 400

        # Envoi de la requête au modèle pour générer la commande Git
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Génère une commande Git pour : {user_prompt}"}],
            model="llama-3.3-70b-versatile"
        )

        # Récupérer la réponse du modèle
        model_response = response.choices[0].message.content

        return jsonify({"response": model_response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Démarrer l'API Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)
