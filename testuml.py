import os
from groq import Groq

# Définir la clé API Groq
api_key = "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"  # Remplacez par votre clé API Groq

# Définir la clé API dans l'environnement
os.environ["GROQ_API_KEY"] = api_key

# Créer une instance du client Groq avec la clé API
client = Groq(api_key=api_key)

# Fonction pour générer un diagramme UML à partir du code
def generate_uml_diagram(code_snippet):
    """
    Envoie un extrait de code Python à l'API Groq pour générer automatiquement un diagramme UML en utilisant Mermaid.js.

    Paramètre:
    code_snippet (str): Le code Python à analyser pour générer le diagramme UML.

    Retourne:
    str: La description UML générée sous forme de texte (Mermaid.js).
    """
    chat_completion = client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": f"Analyse ce code Python et génère un diagramme UML en utilisant Mermaid.js:\n\n{code_snippet}"
        }],
        model="llama-3.3-70b-versatile",  # Modèle utilisé pour la génération du diagramme UML
    )

    return chat_completion.choices[0].message.content

# Exemple de code Python à analyser pour le diagramme UML
code_example = """
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def greet(self):
        print(f'Hello, my name is {self.name} and I am {self.age} years old.')

class Student(Person):
    def __init__(self, name, age, student_id):
        super().__init__(name, age)
        self.student_id = student_id

    def study(self):
        print(f'Studying with student ID: {self.student_id}')
"""

# Génération du diagramme UML en format Mermaid.js
uml_description = generate_uml_diagram(code_example)

# Affichage de la description du diagramme UML (Mermaid.js) dans le terminal
print("Diagramme UML en format Mermaid.js généré :")
print(uml_description)

# Exemple de code Mermaid.js généré (généré par l'API ou défini manuellement)
mermaid_code = """
classDiagram
    class Person {
        +String name
        +int age
        +__init__(name: String, age: int)
        +greet()
    }
    class Student {
        +String student_id
        +__init__(name: String, age: int, student_id: String)
        +study()
    }
    Person <|-- Student
"""

# Enregistrer le code Mermaid.js dans un fichier .mmd
file_path = "C:/Users/USER/Downloads/diagram.mmd"  # Changez ce chemin en fonction de votre répertoire local
with open(file_path, "w") as file:
    file.write(mermaid_code)

# Affichage du fichier généré dans le terminal
print(f"Le diagramme Mermaid.js a été sauvegardé dans {file_path}")

# Instructions pour la visualisation
print("Pour afficher le diagramme, ouvrez le fichier '.mmd' dans VS Code ou utilisez un plugin Mermaid dans VS Code pour la prévisualisation.")
