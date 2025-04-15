from fastapi import FastAPI
from pydantic import BaseModel
import os
from groq import Groq
import sqlite3
import csv
from fastapi.responses import FileResponse
import uvicorn

# ===========================
# 🚀 Initialisation de l'app
# ===========================
app = FastAPI()

# ===========================
# 🔐 Clé API GROQ
# ===========================
api_key = "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"  # ⚠️ À ne pas exposer en production
os.environ["GROQ_API_KEY"] = api_key
client = Groq(api_key=api_key)

# ===========================
# 📦 Modèle Pydantic
# ===========================
class DatabaseRequest(BaseModel):
    comment: str

# ===========================
# 🔗 Connexion base SQLite
# ===========================
def get_db_connection():
    conn = sqlite3.connect("company.db")
    conn.row_factory = sqlite3.Row
    return conn

# ===========================
# 📂 Initialisation des tables si base vide
# ===========================
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Création des tables par défaut
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS job_titles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT
    );

    CREATE TABLE IF NOT EXISTS employé (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT,
        prenom TEXT,
        id_poste INTEGER,
        FOREIGN KEY(id_poste) REFERENCES job_titles(id)
    );
    """)

    # Insertion par défaut si vide
    cursor.execute("SELECT COUNT(*) FROM job_titles")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO job_titles (titre) VALUES ('Développeur'), ('Designer'), ('Chef de projet')")
        cursor.execute("""
            INSERT INTO employé (nom, prenom, id_poste) VALUES
            ('Dupont', 'Jean', 1),
            ('Martin', 'Claire', 2),
            ('Bernard', 'Luc', 3)
        """)

    conn.commit()
    conn.close()

init_db()

# ===========================
# 🧹 Nettoyage SQL généré
# ===========================
def clean_sql_response(response: str) -> str:
    keywords = ["CREATE", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "SELECT"]
    for keyword in keywords:
        if keyword in response.upper():
            index = response.upper().find(keyword)
            return response[index:]
    return response.strip()

# ===========================
# ✨ Génération + Exécution
# ===========================
@app.post("/generate_sql_code")
def generate_and_execute_sql_code(request: DatabaseRequest):
    # Appel LLM
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": request.comment}],
        model="llama-3.3-70b-versatile",
    )

    raw_sql = chat_completion.choices[0].message.content.strip()
    generated_sql_code = clean_sql_response(raw_sql)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Séparer les instructions si multiples
        sql_statements = [stmt.strip() for stmt in generated_sql_code.split(";") if stmt.strip()]
        select_result = None

        for stmt in sql_statements:
            if stmt.upper().startswith("SELECT"):
                cursor.execute(stmt)
                rows = cursor.fetchall()
                if rows:
                    file_path = "resultats.csv"
                    with open(file_path, mode="w", newline="") as file:
                        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
                        writer.writeheader()
                        writer.writerows(rows)
                    conn.close()
                    return FileResponse(file_path, media_type='text/csv', filename="resultats.csv")
            else:
                cursor.execute(stmt)

        conn.commit()
        conn.close()

        return {
            "generated_sql_code": generated_sql_code,
            "execution_status": "Success (no SELECT results)"
        }

    except Exception as e:
        return {
            "generated_sql_code": generated_sql_code,
            "execution_status": "Error",
            "error": str(e)
        }

# ===========================
# 🔥 Lancer le serveur
# ===========================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8755)
