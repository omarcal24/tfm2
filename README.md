# genai-tfm

## Final Master Project - Generative AI

### 🤖 Intelligent Restaurant Reservation Agent


**Para probar los ultimos cambios 9/Enero**:
1. Agente en terminal: python agent/main.py   --> Ejecutará el agente en terminal, podrás interactuar con el y ver el proceso de razonamiento
2. FastAPI en terminal antes de lanzar front: python .\FastAPI\api_server.py
3. Lanzar el Front para interactuar con el agente a traves de FastAPI: streamlit run frontend/frontend.py


POR HACER/SUGERIR:
- Integrar flujo llamadas de voz con twilio y agente
- Integrar todo bajo un mismo script ejecutable
- Terminar de ajustar el Frontend para dejarlo más fino
- montar en nube como aplicación???(megamotivada seria ya)




TO UPDATE BELOW

An autonomous agent built with LangGraph that searches restaurants, checks availability, and makes reservations using natural language.

**Key Features:**
- Natural language understanding (extracts location, date, time, people from conversation)
- Intelligent TOP 3 ranking with LLM reasoning
- Automatic fallback: API → Phone call if needed
- Human-in-the-Loop for critical decisions

---

## 📁 Project Structure
```
genai-tfm/
│
├── agent/                          # Core agent system (LangGraph + ReAct)
│   ├── agent_state.py             # State management and data models
│   ├── agent_prompts.py           # LLM prompts and templates
│   ├── agent_tools.py             # External tools (Google Places, APIs)
│   ├── agent_nodes.py             # 12 intelligence nodes
│   ├── agent_graph.py             # LangGraph orchestration
│   └── agent_main.py              # Agent execution module
│
├── FastAPI/                        # API backend
│   ├── api_server.py              # FastAPI server
│   └── test_api.py                # API tests
│
├── frontend/                       # User interface
│   ├── frontend.py                # Streamlit UI
│   └── logo.jpeg                  # UI assets
|
├── Playground_arena/                        # Testing area
│   ├── playground_arena_notebook.ipynb       # Testing funcion google places
│
├── logs/                           # Execution logs
│
├── .env                            # Environment variables (API keys)
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
├── backend_google_places.py        # Google Places API integration
├── main.py                         # Legacy entry point
├── Playground_notebook.ipynb       # Development notebook with examples of use
├── README.md                       # Project documentation
├── requirements.txt                # Python dependencies
├── run.py                          # Main entry point for agent

```

---

## 🚀 Quick Start

---


### 1. Run the agent in the terminal

**TERMINAL MODE Interactive mode (chat):**
```bash
python run.py --mode interactive
```



**UNTESTED Test mode (automated):**
```bash
python run.py --mode test
```

**UNTESTED Specific test case:**
```bash
python run.py --mode test --test-case complete
```
### 2. Run the API Server

**In the terminal, inside the FastAPI folder:**
```bash
python api_server.py
```
---
