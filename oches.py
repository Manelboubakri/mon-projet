import os
import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from langgraph.graph import StateGraph  # ✅ seul import nécessaire
from typing import TypedDict
# ------------------- CONFIGURATION -------------------

app = FastAPI()

api_key = "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"
os.environ["GROQ_API_KEY"] = api_key
groq_client = Groq(api_key=api_key)

# ------------------- ÉTAT POUR LANGGRAPH -------------------

class CodeState(TypedDict, total=False):
    prompt: str
    description: str
    response: str

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

# ------------------- LANGGRAPH GRAPH -------------------

def build_graph():
    graph = StateGraph(CodeState)
    graph.add_node("correct", lambda state: {"response": correct_code_agent(state["prompt"])} if "corrig" in state["prompt"] else state)
    graph.add_node("generate", lambda state: {"response": generate_code_agent(state.get("description") or state["prompt"])} if "générer" in state["prompt"] else state)
    graph.add_node("git", lambda state: {"response": git_command_agent(state["prompt"])} if "git" in state["prompt"] else state)
    graph.add_node("uml", lambda state: {"response": generate_uml_diagram(state["prompt"])} if "uml" in state["prompt"] else state)
    graph.add_node("test", lambda state: {"response": generate_tests_agent(state["prompt"])} if "test" in state["prompt"] else state)
    graph.add_node("doc", lambda state: {"response": generate_documentation_agent(state["prompt"])} if "doc" in state["prompt"] else state)
    graph.add_node("sql", lambda state: {"response": database_agent(state["prompt"])} if "sql" in state["prompt"] or "base" in state["prompt"] else state)
    graph.set_entry_point("correct")
    graph.add_edge("correct", "generate")
    graph.add_edge("generate", "git")
    graph.add_edge("git", "uml")
    graph.add_edge("uml", "test")
    graph.add_edge("test", "doc")
    graph.add_edge("doc", "sql")
    graph.set_finish_point("sql")
    return graph.compile()

compiled_graph = build_graph()

# ------------------- ENDPOINTS -------------------

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
    uvicorn.run(app, host="0.0.0.0", port=2007)
