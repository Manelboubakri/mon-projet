from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Remplace par le chemin vers ton dossier contenant les fichiers du modèle
model_path = r"C:\Users\USER\Downloads\codegen_project\codegen_model"

# Charger le tokenizer et le modèle à partir du dossier
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

# S'assurer que le modèle utilise le CPU
device = torch.device("cpu")
model.to(device)

def generate_code(comment: str) -> str:
    inputs = tokenizer(comment, return_tensors="pt").to(device)
    outputs = model.generate(**inputs, max_length=150)  # Ajuste la longueur max si nécessaire
    code = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return code

# Test rapide
if __name__ == "__main__":
    prompt = "Créer une fonction qui vérifie si un nombre est premier en Python."
    generated_code = generate_code(prompt)
    print("Code généré :\n", generated_code)
