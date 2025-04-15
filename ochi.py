import os
import sqlite3
import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from langgraph.graph import StateGraph
from typing import TypedDict

# Initialisation de FastAPI
app = FastAPI()

# Clé API Groq
api_key = "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"
os.environ["GROQ_API_KEY"] = api_key
groq_client = Groq(api_key=api_key)

# Base de données SQLite pour l'historique
conn = sqlite3.connect("history.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT,
    response TEXT,
    timestamp TEXT
)
""")
conn.commit()
conn.close()

# État LangGraph
class CodeState(TypedDict, total=False):
    prompt: str
    description: str
    response: str

# Modèle de requête
class CodeRequest(BaseModel):
    prompt: str
    description: str = None

# Fonctions des agents

def correct_code_agent(prompt: str) -> str:
    return groq_client.chat.completions.create(
        messages=[{"role": "user", "content": f"Corrige le code suivant :\n{prompt}"}],
        model="llama-3.3-70b-versatile"
    ).choices[0].message.content

def generate_code_agent(description: str) -> str:
    return groq_client.chat.completions.create(
        messages=[{"role": "user", "content": f"Génère le code suivant en Python : {description}"}],
        model="llama-3.3-70b-versatile"
    ).choices[0].message.content

def git_command_agent(command: str) -> str:
    forbidden = ["reset --hard", "rm -rf", "rebase", "checkout -f"]
    if any(f in command for f in forbidden):
        return f"❌ Commande dangereuse bloquée : '{command}'"
    return groq_client.chat.completions.create(
        messages=[{"role": "user", "content": f"Explique et exécute cette commande Git : {command}"}],
        model="llama-3.3-70b-versatile"
    ).choices[0].message.content

def generate_uml_diagram(code_snippet: str) -> str:
    return groq_client.chat.completions.create(
        messages=[{"role": "user", "content": f"Génère un diagramme UML avec Mermaid.js pour ce code Python :\n{code_snippet}"}],
        model="llama-3.3-70b-versatile"
    ).choices[0].message.content

def generate_tests_agent(code: str) -> str:
    return groq_client.chat.completions.create(
        messages=[{"role": "user", "content": f"Voici un code Python :\n{code}\nGénère des tests unitaires."}],
        model="llama-3.3-70b-versatile"
    ).choices[0].message.content

def generate_documentation_agent(code: str) -> str:
    return groq_client.chat.completions.create(
        messages=[{"role": "user", "content": f"Ajoute des docstrings et de la documentation à ce code Python :\n{code}"}],
        model="llama-3.3-70b-versatile"
    ).choices[0].message.content

def clean_sql_response(response: str) -> str:
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
            return "❌ La requête SQL n'est pas valide."

        conn = sqlite3.connect("company.db")
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        conn.commit()
        conn.close()

        result_str = "\n".join([", ".join(map(str, row)) for row in results])
        return f"✅ Requête SQL :\n{sql}\n📄 Résultats :\n{result_str or 'Aucun'}"
    except Exception as e:
        return f"❌ Erreur SQL : {e}"

# Mémoire & historique
def save_to_history(prompt: str, response: str):
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (prompt, response, timestamp) VALUES (?, ?, ?)",
                   (prompt, response, str(datetime.datetime.now())))
    conn.commit()
    conn.close()

def get_last_response(prompt: str) -> str:
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT response FROM history WHERE prompt LIKE ? ORDER BY id DESC LIMIT 1", (f"%{prompt}%",))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# Planificateur intelligent avec mémoire
def planning_agent(state: CodeState) -> CodeState:
    prompt = state["prompt"].lower()

    # Mémoire : vérifier l'historique
    memory_response = get_last_response(prompt)
    if memory_response:
        return {"response": f"🧠 Réponse retrouvée :\n{memory_response}"}

    if "corrig" in prompt:
        response = correct_code_agent(prompt)
    elif "générer" in prompt:
        description = state.get("description") or prompt
        response = generate_code_agent(description)
        response += "\n\n🧪 **Tests** :\n" + generate_tests_agent(response)
        response += "\n\n📘 **Documentation** :\n" + generate_documentation_agent(response)
    elif "git" in prompt:
        response = git_command_agent(prompt)
    elif "uml" in prompt:
        response = generate_uml_diagram(prompt)
    elif "test" in prompt:
        response = generate_tests_agent(prompt)
    elif "doc" in prompt:
        response = generate_documentation_agent(prompt)
    elif "sql" in prompt or "base" in prompt:
        response = database_agent(prompt)
    else:
        response = "🤖 Je ne comprends pas encore cette tâche."

    save_to_history(prompt, response)
    return {"response": response}

# Graphe LangGraph
def build_graph():
    graph = StateGraph(CodeState)
    graph.add_node("planner", planning_agent)
    graph.set_entry_point("planner")
    graph.set_finish_point("planner")
    return graph.compile()

compiled_graph = build_graph()

# Endpoints FastAPI

@app.post("/predict")
async def predict(request: CodeRequest):
    try:
        result = compiled_graph.invoke({"prompt": request.prompt, "description": request.description})
        return {"response": result.get("response", "❌ Aucun résultat généré")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def get_history():
    conn = sqlite3.connect("history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT prompt, response, timestamp FROM history ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    return {"history": [{"prompt": p, "response": r, "timestamp": t} for p, r, t in rows]}

# Lancement du serveur
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=2007)
