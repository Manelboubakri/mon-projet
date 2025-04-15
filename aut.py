import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from langgraph.graph import StateGraph
from typing import TypedDict, Optional
import logging

# ------------------- CONFIGURATION -------------------
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_key = "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"
os.environ["GROQ_API_KEY"] = api_key
groq_client = Groq(api_key=api_key)

# ------------------- MODELES -------------------
class CodeSnippet(BaseModel):
    code: str

class CodeRequest(BaseModel):
    prompt: str
    description: Optional[str] = None

# ------------------- ETAT POUR LANGGRAPH -------------------
class CodeState(TypedDict):
    prompt: str
    description: Optional[str]
    result: Optional[str]

# ------------------- AGENTS -------------------
def correct_code_agent(prompt: str) -> str:
    try:
        logger.info(f"Sending request to Groq with prompt: {prompt}")
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )
        logger.info(f"Groq response: {response}")
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            logger.error("Empty choices in response")
            return "Aucune réponse de Groq."
    except Exception as e:
        logger.error(f"Error in correct_code_agent: {e}")
        return "Erreur lors de la correction du code."

def generate_code_agent(state: CodeState) -> CodeState:
    prompt = state["prompt"]
    description = state.get("description", "générer du code Python")
    try:
        logger.info(f"Generating code with description: {description}, prompt: {prompt}")
        prompt_groq = f"Écris une fonction Python qui {prompt}."
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_groq}],
            model="llama-3.3-70b-versatile"
        )
        logger.info(f"Groq response: {response}")
        if response.choices and len(response.choices) > 0:
            return {"prompt": prompt, "description": description, "result": response.choices[0].message.content}
        else:
            logger.error("Empty choices in response")
            return {"prompt": prompt, "description": description, "result": "Aucune réponse de Groq."}
    except Exception as e:
        logger.error(f"Error in generate_code_agent: {e}")
        return {"prompt": prompt, "description": description, "result": "Erreur lors de la génération du code."}

def git_command_agent(prompt: str) -> str:
    forbidden = ["reset --hard", "rm -rf", "rebase", "checkout -f"]
    if any(f in prompt for f in forbidden):
        return f"❌ Commande dangereuse bloquée : '{prompt}'"
    try:
        logger.info(f"Executing Git command: {prompt}")
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": f"Exécute la commande Git suivante : {prompt}"}],
            model="llama-3.3-70b-versatile"
        )
        logger.info(f"Git command result: {response}")
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            logger.error("Empty choices in response")
            return "Aucune réponse de Groq."
    except Exception as e:
        logger.error(f"Error in git_command_agent: {e}")
        return "Erreur lors de l'exécution de la commande Git."

def generate_uml_diagram(prompt: str) -> str:
    try:
        logger.info(f"Generating UML diagram for code: {prompt}")
        response = groq_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Analyse ce code Python et génère un diagramme UML en utilisant Mermaid.js:\n\n{prompt}"
            }],
            model="llama-3.3-70b-versatile",
        )
        logger.info(f"UML diagram result: {response}")
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            logger.error("Empty choices in response")
            return "Aucune réponse de Groq."
    except Exception as e:
        logger.error(f"Error in generate_uml_diagram: {e}")
        return "Erreur lors de la génération du diagramme UML."

def generate_tests_agent(prompt: str) -> str:
    try:
        logger.info(f"Generating unit tests for code: {prompt}")
        response = groq_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Voici un code Python :\n{prompt}\nGénère des tests unitaires pour ce code."
            }],
            model="llama-3.3-70b-versatile"
        )
        logger.info(f"Tests generated: {response}")
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            logger.error("Empty choices in response")
            return "Aucune réponse de Groq."
    except Exception as e:
        logger.error(f"Error in generate_tests_agent: {e}")
        return "Erreur lors de la génération des tests unitaires."

def generate_documentation_agent(prompt: str) -> str:
    try:
        logger.info(f"Generating documentation for code: {prompt}")
        response = groq_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Voici un code Python :\n{prompt}\nGénère de la documentation pour ce code."
            }],
            model="llama-3.3-70b-versatile",
        )
        logger.info(f"Documentation generated: {response}")
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content.strip()
        else:
            logger.error("Empty choices in response")
            return "Aucune réponse de Groq."
    except Exception as e:
        logger.error(f"Error in generate_documentation_agent: {e}")
        return "Erreur lors de la génération de la documentation."

# ------------------- AGENT DE DECISION AUTOMATIQUE -------------------
def router_node(state: CodeState) -> dict:
    logger.info(f"Router received state: {state}")
    prompt = state["prompt"].lower()
    if "corrige" in prompt or "corriger" in prompt:
        return {"__next__": "correct_code"}
    elif "générer" in prompt or "fonction" in prompt:
        return {"__next__": "generate_code"}
    elif "git" in prompt:
        return {"__next__": "git_command"}
    elif "uml" in prompt or "diagramme" in prompt:
        return {"__next__": "uml"}
    elif "test" in prompt:
        return {"__next__": "tests"}
    elif "documentation" in prompt or "docstring" in prompt:
        return {"__next__": "doc"}
    else:
        return {"__next__": "end"}

# ------------------- NODES LANGGRAPH -------------------
def node_correct_code(state: CodeState) -> CodeState:
    return {"prompt": state["prompt"], "description": state.get("description"), "result": correct_code_agent(state["prompt"])}

def node_generate_code(state: CodeState) -> CodeState:
    return generate_code_agent(state)

def node_git_command(state: CodeState) -> CodeState:
    return {"prompt": state["prompt"], "description": state.get("description"), "result": git_command_agent(state["prompt"])}

def node_uml(state: CodeState) -> CodeState:
    return {"prompt": state["prompt"], "description": state.get("description"), "result": generate_uml_diagram(state["prompt"])}

def node_tests(state: CodeState) -> CodeState:
    return {"prompt": state["prompt"], "description": state.get("description"), "result": generate_tests_agent(state["prompt"])}

def node_doc(state: CodeState) -> CodeState:
    return {"prompt": state["prompt"], "description": state.get("description"), "result": generate_documentation_agent(state["prompt"])}

def node_end(state: CodeState) -> CodeState:
    return state

# ------------------- GRAPH LANGGRAPH -------------------
builder = StateGraph(CodeState)
builder.set_entry_point("router")

builder.add_node("router", router_node)
builder.add_node("correct_code", node_correct_code)
builder.add_node("generate_code", node_generate_code)
builder.add_node("git_command", node_git_command)
builder.add_node("uml", node_uml)
builder.add_node("tests", node_tests)
builder.add_node("doc", node_doc)
builder.add_node("end", node_end)

builder.add_conditional_edges(
    "router",
    lambda state: state["__next__"],
    {
        "correct_code": "correct_code",
        "generate_code": "generate_code",
        "git_command": "git_command",
        "uml": "uml",
        "tests": "tests",
        "doc": "doc",
        "end": "end",
    },
)

builder.set_finish_point("end")

graph = builder.compile()

# ------------------- ENDPOINT FASTAPI -------------------
@app.post("/predict")
async def predict(request: CodeRequest):
    try:
        input_data: CodeState = {"prompt": request.prompt, "description": request.description, "result": None}
        logger.info(f"Input data: {input_data}")
        result = graph.invoke(input_data)
        logger.info(f"Graph result: {result}")
        return {"response": result["result"]}
    except Exception as e:
        logger.error(f"Error during graph execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    uvicorn.run(app, host="0.0.0.0", port=7500)