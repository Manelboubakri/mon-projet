```mermaid
graph TD
    subgraph FastAPI_App
        A[FastAPI /predict endpoint] --> B[Invoke LangGraph]
        A2[FastAPI /groq_status endpoint]
    end

    subgraph LangGraph
        B --> R[Router Node]
        R -->|corrige| C1[Correct Code Agent]
        R -->|générer| C2[Generate Code Agent]
        R -->|git| C3[Git Command Agent]
        R -->|uml| C4[UML Diagram Agent]
        R -->|test| C5[Generate Tests Agent]
        R -->|doc| C6[Documentation Agent]
        R -->|default| C7[End Node]

        C1 --> E1[Return State]
        C2 --> E2[Return State]
        C3 --> E3[Return State]
        C4 --> E4[Return State]
        C5 --> E5[Return State]
        C6 --> E6[Return State]
        C7 --> E7[Return Final State]
    end

    subgraph Agents
        C1 --> G1[Groq API: Correction]
        C2 --> G2[Groq API: Code Generation]
        C3 --> G3[Groq API: Git Command]
        C4 --> G4[Groq API: UML Diagram]
        C5 --> G5[Groq API: Tests]
        C6 --> G6[Groq API: Documentation]
    end

    subgraph Configuration
        Z1[Logging Config]
        Z2[Set GROQ_API_KEY]
        Z3[Groq Client Init]
    end

