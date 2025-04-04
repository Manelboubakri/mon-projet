from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

app = FastAPI()

# Charger le modèle localement
model_path = r"C:\Users\USER\Downloads\codegen_project\codegen_model"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

# Forcer l'utilisation du CPU
device = torch.device("cpu")
model.to(device)

# Définir le format des requêtes
class CodeRequest(BaseModel):
    comment: str

@app.post("/generate_code")
def generate_code(request: CodeRequest):
    inputs = tokenizer(request.comment, return_tensors="pt").to(device)
    outputs = model.generate(**inputs, max_length=150)
    code = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return {"generated_code": code}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Port modifié à 8000
    
