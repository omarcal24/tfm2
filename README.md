# genai-tfm

## Final Master Project - Generative AI

### 🤖 Intelligent Restaurant Reservation Agent

**Para probar los ultimos cambios 9/Enero**:

1. Agente en terminal: python agent/main.py --> Ejecutará el agente en terminal, podrás interactuar con el y ver el proceso de razonamiento
2. FastAPI en terminal antes de lanzar front: python .\FastAPI\api_server.py
3. Lanzar el Front para interactuar con el agente a traves de FastAPI: streamlit run frontend/frontend.py

**Instrucciones para generar las credenciales de Google Calendar**

1.  Crea un proyecto nuevo en https://console.cloud.google.com/
2.  Habilita la API: Ve a "APIs y servicios" > "Biblioteca", busca "Google Calendar API" y habilítala.
3.  Pantalla de Consentimiento OAuth:
    1. Ve a "APIs y servicios" > "Pantalla de consentimiento de OAuth".
    2. Selecciona el tipo de usuario (interno o externo).
    3. Configura el nombre de la aplicación, y la información de contacto.
    4. Dale permisos completos, la aplicación configurará luego los SCOPES
4.  Crea Credenciales OAuth:
    1. Ve a "APIs y servicios" > "Credenciales" > "Crear credenciales" > "ID de cliente OAuth".
    2. Elige el tipo de aplicación: Web application
    3. Añade las URIs de redireccionamiento autorizadas (donde Google devolverá el código de autorización):
       - http://localhost/8080/
       - http://127.0.0.1/8080/
    4. Guarda el ID de cliente y el Secreto de cliente ("credentials.json) que se generan, son cruciales para tu aplicación.
    5. Coloca el fichero credentials.json en el directorio raiz de tu proyecto
5.  Ve a Google Auth Platform -> Público -> Haz scroll down hasta "Usuarios de prueba"
    1.  Añade tu cuenta de google: xxxx@gmail.com que estés utilizando para correr la aplicación

**Instrucciones para habilitar Google Places API**

1. Ve a google maps platform https://console.cloud.google.com/google/maps-apis/overview
   1. Asegúrate que utilizas el mismo proyecto en que habilitaste google calendar API
   2. La primera vez te pedirá crear un clave de api, esa es la variable de entorno GOOGLE_MAPS_API_KEY
      - Debes implementar una restricción por IP, y agregar tu IP pública
      - Debes implementar una restricción de API para las siguientes APIs:
        - Distance Matrix API
        - Geocoding API
        - Places API (New)
   3. Puedes revisar, o rehacer tus credenciales en APIs y Servicios -> Credenciales -> Nueva Clave de API
2. En APIs y Servicios -> Biblioteca habilita las siguientes APIs
   - Geocoding API (necesaria para convertir direcciones a coordenadas)
   - Places API (New) o Places API (para búsqueda de lugares)
   - Distance Matrix API (para filtrado por tiempo de viaje)

POR HACER/SUGERIR:

- Integrar flujo llamadas de voz con twilio y agente
- Integrar todo bajo un mismo script ejecutable - TENEMOS VARIOS main.py ESTO NO PUEDE SER
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
