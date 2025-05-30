import os
import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from langgraph.graph import StateGraph

# ------------------- CONFIGURATION -------------------

app = FastAPI()

# Clé API Groq (⚠️ stocker dans un environnement sécurisé en production)
api_key = "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"
os.environ["GROQ_API_KEY"] = api_key
groq_client = Groq(api_key=api_key)

# ------------------- MODELES -------------------

class CodeSnippet(BaseModel):
    code: str

class CodeRequest(BaseModel):
    prompt: str
    description: str = None

# ------------------- AGENTS -------------------

def correct_code_agent(prompt: str) -> str:
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )
    return response.choices[0].message.content

def generate_code_agent(description: str) -> str:
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": f"Peux-tu me générer {description} en Python ?"}],
        model="llama-3.3-70b-versatile"
    )
    return response.choices[0].message.content

def git_command_agent(command: str) -> str:
    forbidden = ["reset --hard", "rm -rf", "rebase", "checkout -f"]
    if any(f in command for f in forbidden):
        return f"❌ Commande dangereuse bloquée : '{command}'"
    try:
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": f"Exécute la commande Git suivante : {command}"}],
            model="llama-3.3-70b-versatile"
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Exception système : {e}"

def generate_uml_diagram(code_snippet: str) -> str:
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Analyse ce code Python et génère un diagramme UML en utilisant Mermaid.js:\n\n{code_snippet}"
            }],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du diagramme UML: {e}")

def generate_tests_agent(code: str) -> str:
    try:
        response = groq_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Voici un code Python :\n{code}\nGénère des tests unitaires pour ce code."
            }],
            model="llama-3.3-70b-versatile"
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération des tests unitaires: {e}")

def generate_documentation_agent(code: str) -> str:
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Voici un code Python :\n{code}\nGénère de la documentation pour ce code en ajoutant des docstrings et des commentaires."
            }],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération de la documentation: {e}")

# ------------------- AGENT BASE DE DONNÉES -------------------

def clean_sql_response(response: str) -> str:
    """
    Nettoie une réponse SQL générée par un LLM en retirant le texte explicatif ou décoratif.
    Garde uniquement la requête SQL.
    """
    lines = response.strip().splitlines()
    sql_lines = [line for line in lines if line.strip().lower().startswith("create") or ";" in line]
    return "\n".join(sql_lines).strip()

def database_agent(comment: str) -> str:
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": comment}],
            model="llama-3.3-70b-versatile"
        )
        raw_sql = chat_completion.choices[0].message.content.strip()
        sql = clean_sql_response(raw_sql)

        if not sql.lower().startswith("create table"):
            return "❌ La requête SQL générée n'est pas valide pour créer une table. Vérifiez la syntaxe."

        conn = sqlite3.connect("company.db")
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description] if cursor.description else []

        conn.commit()
        conn.close()

        if results:
            result_str = "\n".join([", ".join(map(str, row)) for row in results])
            return f"✅ Requête exécutée avec succès :\n{sql}\n\n📄 Résultats :\n{result_str}"
        else:
            return f"✅ Requête exécutée :\n{sql}\nAucun résultat à afficher."

    except Exception as e:
        return f"❌ Erreur lors de l'exécution de la requête : {e}"

# ------------------- ORCHESTRATEUR -------------------

def orchestrator(request_data: dict) -> str:
    try:
        prompt = request_data.get("prompt", "").strip().lower()

        if "corrige" in prompt or "corriger" in prompt:
            return correct_code_agent(request_data["prompt"])
        elif "générer" in prompt or "fonction" in prompt:
            return generate_code_agent(request_data.get("description") or prompt)
        elif prompt.startswith("git") or "commande git" in prompt:
            return git_command_agent(prompt)
        elif "uml" in prompt or "diagramme" in prompt:
            return generate_uml_diagram(request_data["prompt"])
        elif "test" in prompt or "unitaire" in prompt:
            return generate_tests_agent(request_data["prompt"])
        elif "documentation" in prompt or "documenter" in prompt:
            return generate_documentation_agent(request_data["prompt"])
        elif "requête" in prompt or "sql" in prompt or "base de données" in prompt:
            return database_agent(request_data["prompt"])
        else:
            return "❌ Action non reconnue. Veuillez fournir un prompt plus spécifique."
    except Exception as e:
        return f"❌ Erreur : {e}"

# ------------------- ENDPOINTS -------------------

@app.post("/predict")
async def predict(request: CodeRequest):
    try:
        response = orchestrator(request.dict())
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_uml")
async def generate_uml(request: CodeSnippet):
    code_snippet = request.code
    uml_description = generate_uml_diagram(code_snippet)
    mermaid_code = f"""
    classDiagram
        {uml_description}
    """
    return {
        "message": "Diagramme Mermaid.js généré avec succès",
        "uml_code": mermaid_code.strip()
    }

@app.post("/generate_tests")
async def generate_tests(request: CodeSnippet):
    tests = generate_tests_agent(request.code)
    return {
        "message": "Tests unitaires générés avec succès",
        "tests": tests
    }

@app.post("/generate_code")
async def generate_code(request: CodeRequest):
    code = generate_code_agent(request.description or request.prompt)
    return {
        "message": "Code généré avec succès",
        "code": code
    }

@app.post("/correct_code")
async def correct_code(request: CodeSnippet):
    corrected = correct_code_agent(request.code)
    return {
        "message": "Code corrigé avec succès",
        "corrected_code": corrected
    }

@app.post("/git_command")
async def run_git_command(request: CodeSnippet):
    result = git_command_agent(request.code)
    return {
        "message": "Commande Git traitée",
        "result": result
    }

@app.post("/generate_documentation")
async def generate_documentation(request: CodeSnippet):
    documentation = generate_documentation_agent(request.code)
    return {
        "message": "Documentation générée avec succès",
        "documentation": documentation
    }

@app.post("/database_query")
async def database_query(request: CodeRequest):
    response = database_agent(request.prompt)
    return {
        "message": "Requête SQL traitée",
        "result": response
    }

@app.get("/groq_status")
async def get_groq_status():
    return {
        "status": "success",
        "api_key": os.environ.get("GROQ_API_KEY"),
        "message": "API Groq est opérationnelle"
    }

# ------------------- LANCEMENT LOCAL -------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8098)
