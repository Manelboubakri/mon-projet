import os
import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from langgraph.graph import StateGraph
from typing import TypedDict

app = FastAPI()

# --- Configuration de l'API Groq ---
api_key = "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"
os.environ["GROQ_API_KEY"] = api_key
groq_client = Groq(api_key=api_key)

# --- État LangGraph ---
class CodeState(TypedDict, total=False):
    prompt: str
    description: str
    response: str

# --- Modèles ---
class CodeRequest(BaseModel):
    prompt: str
    description: str = None

# --- Agents (fonctions individuelles) ---
def correct_code_agent(prompt: str) -> str:
    return groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    ).choices[0].message.content

def generate_code_agent(description: str) -> str:
    return groq_client.chat.completions.create(
        messages=[{"role": "user", "content": f"Peux-tu me générer {description} en Python ?"}],
        model="llama-3.3-70b-versatile"
    ).choices[0].message.content

def git_command_agent(command: str) -> str:
    forbidden = ["reset --hard", "rm -rf", "rebase", "checkout -f"]
    if any(f in command for f in forbidden):
        return f"❌ Commande dangereuse bloquée : '{command}'"
    return groq_client.chat.completions.create(
        messages=[{"role": "user", "content": f"Exécute la commande Git suivante : {command}"}],
        model="llama-3.3-70b-versatile"
    ).choices[0].message.content

def generate_uml_diagram(code_snippet: str) -> str:
    return groq_client.chat.completions.create(
        messages=[{"role": "user", "content": f"Analyse ce code Python et génère un diagramme UML avec Mermaid.js :\n\n{code_snippet}"}],
        model="llama-3.3-70b-versatile"
    ).choices[0].message.content

def generate_tests_agent(code: str) -> str:
    return groq_client.chat.completions.create(
        messages=[{"role": "user", "content": f"Voici un code Python :\n{code}\nGénère des tests unitaires pour ce code."}],
        model="llama-3.3-70b-versatile"
    ).choices[0].message.content.strip()

def generate_documentation_agent(code: str) -> str:
    return groq_client.chat.completions.create(
        messages=[{"role": "user", "content": f"Voici un code Python :\n{code}\nAjoute de la documentation et des docstrings."}],
        model="llama-3.3-70b-versatile"
    ).choices[0].message.content.strip()

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

# --- Agent de planification intelligent ---
def planning_agent(state: CodeState) -> CodeState:
    prompt = state["prompt"].lower()

    if "corrig" in prompt:
        return {"response": correct_code_agent(prompt)}
    elif "générer" in prompt:
        response = generate_code_agent(state.get("description") or prompt)
        # Appelle tests et doc si code généré
        test_response = generate_tests_agent(response)
        doc_response = generate_documentation_agent(response)
        return {"response": f"{response}\n\n🧪 Tests :\n{test_response}\n\n📘 Doc :\n{doc_response}"}
    elif "git" in prompt:
        return {"response": git_command_agent(prompt)}
    elif "uml" in prompt:
        return {"response": generate_uml_diagram(prompt)}
    elif "test" in prompt:
        return {"response": generate_tests_agent(prompt)}
    elif "doc" in prompt:
        return {"response": generate_documentation_agent(prompt)}
    elif "sql" in prompt or "base" in prompt:
        return {"response": database_agent(prompt)}
    else:
        return {"response": "🤖 Je ne comprends pas la tâche demandée."}

# --- Graphe LangGraph ---
def build_graph():
    graph = StateGraph(CodeState)
    graph.add_node("planner", planning_agent)
    graph.set_entry_point("planner")
    graph.set_finish_point("planner")
    return graph.compile()

compiled_graph = build_graph()

# --- API Endpoints ---
@app.post("/predict")
async def predict(request: CodeRequest):
    try:
        result = compiled_graph.invoke({"prompt": request.prompt, "description": request.description})
        return {"response": result.get("response", "❌ Aucun résultat généré")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/groq_status")
async def get_groq_status():
    return {
        "status": "success",
        "api_key": os.environ.get("GROQ_API_KEY"),
        "message": "API Groq est opérationnelle"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2450)
