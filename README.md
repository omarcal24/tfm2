# 🍽️ FoodLooker

**Agente Inteligente de Reservas con IA**
*Trabajo Final de Máster*

FoodLooker es un sistema de agente conversacional inteligente que ayuda a los usuarios a encontrar y reservar restaurantes utilizando IA generativa. Combina modelos de lenguaje (LLMs) con integraciones de servicios externos para proporcionar una experiencia de reserva completa y automatizada.

---

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Stack Tecnológico](#-stack-tecnológico)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Ejecución del Proyecto](#-ejecución-del-proyecto)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Testing](#-testing)
- [Herramientas del Agente](#-herramientas-del-agente)
- [Documentación Adicional](#-documentación-adicional)

---

## ✨ Características Principales

- **Agente Conversacional IA**: Utiliza el patrón ReAct (Reasoning + Acting) con LangGraph para razonamiento inteligente
- **Búsqueda de Restaurantes**: Integración con Google Maps/Places API para encontrar restaurantes según criterios del usuario
- **Reservas Automatizadas**:
  - Sistema de reservas online (mock para demostración)
  - Llamadas telefónicas automatizadas vía Twilio + ElevenLabs (text-to-speech)
- **Gestión de Calendario**: Integración con Google Calendar para programar reservas
- **Búsqueda Web**: Capacidad de buscar información adicional usando Tavily API
- **Interfaz Web**: Frontend interactivo con Streamlit
- **API REST**: Backend con FastAPI para integración con otros sistemas
- **Testing Completo**: Suite de tests unitarios e integración con pytest

---

## 🏗️ Arquitectura del Sistema

FoodLooker implementa un patrón **ReAct Agent** usando LangGraph:

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (Streamlit)                   │
│                   http://localhost:8501                  │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Backend API (FastAPI)                       │
│              http://localhost:8000                       │
│         POST /api/reservation-requests                   │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│            Agent Graph (LangGraph + ReAct)               │
│                                                          │
│  ┌──────────┐         ┌──────────┐        ┌──────────┐ │
│  │  Brain   │────────>│ Execute  │───────>│ Respond  │ │
│  │  Node    │         │  Node    │        │   Node   │ │
│  │  (LLM)   │         │ (Tools)  │        │ (Reply)  │ │
│  └──────────┘         └──────────┘        └──────────┘ │
│       ▲                    │                            │
│       └────────────────────┘                            │
│            (Loop hasta completar)                       │
└──────────────────────────┬──────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
    ┌──────────┐   ┌─────────────┐  ┌──────────┐
    │ Google   │   │   Twilio    │  │ Tavily   │
    │Maps/Cal. │   │+ElevenLabs  │  │  Search  │
    └──────────┘   └─────────────┘  └──────────┘
```

### Flujo de Ejecución

1. **Brain Node**: El LLM analiza el contexto de la conversación y decide la siguiente acción (buscar, reservar, llamar, responder)
2. **Execute Node**: Ejecuta la herramienta seleccionada (maps_search, check_availability, make_booking, phone_call, etc.)
3. **Respond Node**: Envía mensaje al usuario
4. **State Management**: AgentState transporta mensajes, conocimiento y resultados a través del grafo

---

## 🛠️ Stack Tecnológico

### Core AI/ML
- **Python 3.11+**: Lenguaje principal
- **LangGraph**: Orquestación de agentes y flujos
- **LangChain**: Framework de IA para LLMs
- **OpenAI GPT-4o-mini**: Modelo de lenguaje

### Backend & API
- **FastAPI**: Framework web para API REST
- **Uvicorn**: Servidor ASGI
- **Flask**: Servidor para servicio de llamadas
- **Pydantic**: Validación de datos

### Frontend
- **Streamlit**: Interfaz web interactiva

### Servicios Externos
- **Google Maps/Places API**: Búsqueda de restaurantes
- **Google Calendar API**: Gestión de eventos
- **Twilio**: Llamadas telefónicas
- **ElevenLabs**: Text-to-speech
- **Tavily**: Búsqueda web
- **Ngrok**: Tunneling para webhooks

### Testing & Observabilidad
- **pytest**: Framework de testing
- **pytest-asyncio**: Tests asíncronos
- **pytest-cov**: Cobertura de código
- **LangSmith**: Trazabilidad de agentes (opcional)

---

## 📦 Requisitos Previos

- Python 3.11 o superior
- Cuenta de Google Cloud (para Maps y Calendar APIs)
- Cuenta de OpenAI (para GPT-4o-mini)
- Cuenta de Twilio (para llamadas telefónicas)
- Cuenta de ElevenLabs (para text-to-speech)
- Cuenta de Tavily (para búsqueda web)
- Docker (opcional, para ejecución en contenedor)

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd api
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuración

### 1. Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto usando `.env.example` como plantilla:

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales:

```env
# OpenAI
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4o-mini

# Google Maps/Places
GOOGLE_MAPS_API_KEY=AIza...

# Google Calendar
GOOGLE_CREDENTIALS=credentials.json

# Twilio (Phone Calls)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
FROM_TWILIO_PHONE_NUMBER=+1...

# ElevenLabs (Text-to-Speech)
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...

# Tavily (Web Search)
TAVILY_API_KEY=tvly-...

# API Configuration
FAST_API_API_HOST=0.0.0.0
FAST_API_API_PORT=8000
STREAMLIT_PORT=8501

# LangSmith (Optional - for tracing)
LANGSMITH_API_KEY=...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=FoodLooker
```

### 2. Configurar Google Calendar API

#### Paso 1: Crear proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente

#### Paso 2: Habilitar Google Calendar API

1. Ve a **APIs y servicios** > **Biblioteca**
2. Busca **Google Calendar API**
3. Haz clic en **Habilitar**

#### Paso 3: Configurar pantalla de consentimiento OAuth

1. Ve a **APIs y servicios** > **Pantalla de consentimiento de OAuth**
2. Selecciona el tipo de usuario:
   - **Interno**: Solo usuarios de tu organización
   - **Externo**: Cualquier usuario con cuenta de Google
3. Completa la información requerida:
   - Nombre de la aplicación: `FoodLooker`
   - Correo de soporte
   - Información de contacto del desarrollador
4. Configura los permisos necesarios (la aplicación configurará los SCOPES automáticamente)
5. Guarda los cambios

#### Paso 4: Crear credenciales OAuth 2.0

1. Ve a **APIs y servicios** > **Credenciales**
2. Haz clic en **Crear credenciales** > **ID de cliente OAuth**
3. Selecciona **Aplicación web**
4. Agrega las URIs de redireccionamiento autorizadas:
   ```
   http://localhost:8080/
   http://127.0.0.1:8080/
   ```
5. Haz clic en **Crear**
6. Descarga el archivo JSON de credenciales
7. Renombra el archivo a `credentials.json`
8. Coloca `credentials.json` en la raíz del proyecto

#### Paso 5: Agregar usuarios de prueba

1. Ve a **Google Auth Platform** > **Público**
2. Desplázate hasta **Usuarios de prueba**
3. Agrega tu cuenta de Google (ej: `tu-email@gmail.com`)

### 3. Configurar Google Places API

#### Paso 1: Habilitar APIs necesarias

1. Ve a [Google Maps Platform](https://console.cloud.google.com/google/maps-apis/overview)
2. Asegúrate de estar en el mismo proyecto que Google Calendar
3. En **APIs y servicios** > **Biblioteca**, habilita:
   - **Geocoding API** (convertir direcciones a coordenadas)
   - **Places API (New)** o **Places API** (búsqueda de lugares)
   - **Distance Matrix API** (filtrado por tiempo de viaje)

#### Paso 2: Crear API Key

1. Ve a **APIs y servicios** > **Credenciales**
2. Haz clic en **Crear credenciales** > **Clave de API**
3. Copia la clave generada (esta es `GOOGLE_MAPS_API_KEY`)

#### Paso 3: Restringir API Key (Recomendado)

1. Haz clic en la API Key recién creada
2. En **Restricciones de la aplicación**:
   - Selecciona **Direcciones IP**
   - Agrega tu IP pública
3. En **Restricciones de API**:
   - Selecciona **Restringir clave**
   - Marca las siguientes APIs:
     - Distance Matrix API
     - Geocoding API
     - Places API (New)
4. Guarda los cambios

---

## 💻 Ejecución del Proyecto

### Opción 1: Ejecución Completa (Recomendado)

Ejecuta todos los servicios con un solo comando:

```bash
python main.py
```

Este comando inicia:
- Backend API (FastAPI) en `http://localhost:8000`
- Frontend (Streamlit) en `http://localhost:8501`
- Servicio de llamadas (Flask) en `http://localhost:8002`

**Accede a la aplicación**:
- 🖥️ **Frontend**: http://localhost:8501
- 📡 **Backend API**: http://localhost:8000
- 📖 **API Docs**: http://localhost:8000/docs

### Opción 2: Ejecución Individual (Debug)

Para debuguear componentes por separado:

#### 1. Agente en Terminal

```bash
python agent/main.py
```

Ejecuta el agente en modo terminal para ver el proceso de razonamiento completo.

#### 2. Backend API

```bash
python -m uvicorn FastAPI.api_server:app --host 0.0.0.0 --port 8000
```

o

```bash
python FastAPI/api_server.py
```

#### 3. Frontend

```bash
streamlit run frontend/frontend.py
```

#### 4. Servicio de Llamadas

```bash
python backend/call_service.py
```

### Opción 3: Ejecución con Docker

Docker simplifica la ejecución pero **NO carga Streamlit ni Google Calendar** (por limitaciones de autenticación OAuth).

#### Construir la imagen

```bash
docker build -t foodlooker .
```

#### Ejecutar el contenedor

```bash
docker run -p 8000:8000 -p 8501:8501 --env-file .env foodlooker
```

**Acceso**:
- 🖥️ **Frontend**: http://localhost:8501 (limitado)
- 📡 **Backend API**: http://localhost:8000
- 📖 **API Docs**: http://localhost:8000/docs

Ver [INSTRUCCIONES_DOCKER.md](INSTRUCCIONES_DOCKER.md) para más detalles.

---

## 📁 Estructura del Proyecto

```
api/
│
├── agent/                          # Sistema núcleo del agente (LangGraph + ReAct)
│   ├── graph.py                   # Orquestación con LangGraph (brain/execute/respond)
│   ├── main.py                    # Entry point para ejecución en terminal
│   ├── prompts.py                 # Cargador y formateador de prompts
│   ├── state.py                   # Gestión de estado (AgentState TypedDict)
│   └── tools.py                   # Implementación de herramientas externas
│
├── backend/                        # Servicios backend e integraciones
│   ├── calendar_tools.py          # Integración con Google Calendar
│   ├── call_service.py            # Servicio de llamadas (Flask + Twilio + ElevenLabs)
│   └── google_places.py           # Wrapper de Google Places API
│
├── config/
│   └── settings.py                # Cargador de configuración desde .env
│
├── FastAPI/                        # Backend API REST
│   ├── api_server.py              # Servidor FastAPI con endpoints
│   └── test_api.py                # Tests manuales de API
│
├── frontend/                       # Interfaz de usuario
│   ├── frontend.py                # Aplicación Streamlit (chat interactivo)
│   ├── frontend_api_helpers.py    # Funciones helper para llamadas API
│   └── logo.png                   # Logo de la aplicación
│
├── prompts/                        # Plantillas de prompts (Markdown)
│   ├── agent_system_prompt.md     # Prompt del sistema principal del agente
│   ├── call_script_generation.md  # Template para generar scripts de llamadas
│   └── call_result_analysis.md    # Template para analizar resultados de llamadas
│
├── tests/                          # Suite de tests automatizados
│   ├── conftest.py                # Fixtures compartidos y mocks
│   │
│   ├── unit/                      # Tests unitarios
│   │   ├── test_agent_graph.py   # Tests de lógica del grafo del agente
│   │   ├── test_tools.py         # Tests de herramientas del agente
│   │   ├── test_state.py         # Tests de gestión de estado
│   │   ├── test_prompts.py       # Tests del sistema de prompts
│   │   └── test_settings.py      # Tests de configuración
│   │
│   ├── integration/               # Tests de integración
│   │   ├── test_google_places.py # Tests de Google Places API
│   │   ├── test_call_service.py  # Tests del servicio de llamadas
│   │   ├── test_calendar_tools.py# Tests de integración con Calendar
│   │   └── test_api_server.py    # Tests de endpoints de FastAPI
│   │
│   └── fixtures/                  # Datos de prueba
│       └── mock_responses.py     # Respuestas simuladas de APIs
│
├── .coveragerc                     # Configuración de cobertura (salida en test_results/)
├── .env                            # Variables de entorno (NO en git)
├── .env.example                    # Template de variables de entorno
├── .gitignore                      # Archivos ignorados por git
├── .streamlit/
│   └── config.toml                # Configuración de Streamlit
├── Dockerfile                      # Configuración de Docker
├── INSTRUCCIONES_DOCKER.md         # Guía de Docker
├── main.py                         # Entry point principal (orquesta todos los servicios)
├── pytest.ini                      # Configuración de pytest
├── README.md                       # Esta documentación
├── requirements.txt                # Dependencias de Python
└── tool_descriptions.md            # Descripción detallada de herramientas del agente
```

---

## 🧪 Testing

El proyecto incluye una suite completa de tests automatizados usando pytest. Los resultados se generan en `test_results/`.

### Instalación de dependencias de testing

```bash
pip install -r requirements.txt
```

Las dependencias de testing incluyen:
- `pytest>=7.0.0`
- `pytest-asyncio`
- `pytest-mock`
- `pytest-cov`

### Ejecutar tests

#### Todos los tests

```bash
pytest
```

#### Solo tests unitarios

```bash
pytest tests/unit/
```

#### Solo tests de integración

```bash
pytest tests/integration/
```

#### Con cobertura de código

```bash
pytest --cov
```

El reporte HTML de cobertura se genera en `test_results/htmlcov/index.html`

#### Test específico con verbose

```bash
pytest tests/unit/test_agent_graph.py -v
```

#### Generar reporte JUnit XML (para CI/CD)

```bash
pytest --junitxml=test_results/junit.xml
```

### Resultados de tests

Los resultados se guardan en:
- **`test_results/htmlcov/`**: Reporte HTML de cobertura
- **`test_results/.coverage`**: Datos binarios de cobertura
- **`test_results/junit.xml`**: Reporte JUnit (opcional)

### Estructura de tests

- **`tests/unit/`**: Tests unitarios que verifican componentes individuales
  - `test_agent_graph.py`: Lógica del grafo del agente
  - `test_tools.py`: Funciones de herramientas
  - `test_state.py`: Gestión de estado
  - `test_prompts.py`: Sistema de prompts
  - `test_settings.py`: Carga de configuración

- **`tests/integration/`**: Tests de integración con servicios externos (usando mocks)
  - `test_google_places.py`: Google Places API
  - `test_call_service.py`: Servicio de llamadas
  - `test_calendar_tools.py`: Google Calendar
  - `test_api_server.py`: Endpoints de FastAPI

- **`tests/conftest.py`**: Fixtures compartidos y configuración de mocks

---

## 🔧 Herramientas del Agente

El agente tiene acceso a 7 herramientas principales:

### 1. `web_search`
Busca información en la web usando Tavily API.

**Uso**: Cuando el usuario solicita información que no está en el conocimiento del agente.

### 2. `maps_search`
Busca restaurantes usando Google Maps/Places API.

**Parámetros**:
- `location`: Ubicación del usuario
- `keywords`: Tipo de comida, nombre del restaurante, etc.
- `max_results`: Número máximo de resultados (default: 5)

### 3. `check_availability`
Verifica disponibilidad de un restaurante (sistema mock).

**Parámetros**:
- `restaurant_name`: Nombre del restaurante
- `date`: Fecha de la reserva
- `time`: Hora de la reserva
- `party_size`: Número de personas

### 4. `make_booking`
Realiza una reserva en el sistema mock.

**Parámetros**:
- `restaurant_name`: Nombre del restaurante
- `date`: Fecha de la reserva
- `time`: Hora de la reserva
- `party_size`: Número de personas
- `customer_name`: Nombre del cliente
- `customer_phone`: Teléfono del cliente

### 5. `phone_call`
Realiza una llamada telefónica automatizada usando Twilio y ElevenLabs.

**Parámetros**:
- `to_number`: Número de teléfono del restaurante
- `call_purpose`: Propósito de la llamada
- `restaurant_name`: Nombre del restaurante
- `date`, `time`, `party_size`, `customer_name`, `customer_phone`: Detalles de la reserva

⚠️ **Advertencia**: Esta función realiza llamadas reales. Usar con precaución.

### 6. `create_calendar_event`
Crea un evento en Google Calendar.

**Parámetros**:
- `summary`: Título del evento
- `location`: Ubicación
- `description`: Descripción
- `start_time`: Fecha/hora de inicio (ISO 8601)
- `end_time`: Fecha/hora de fin (ISO 8601)

### 7. `respond`
Envía un mensaje de texto al usuario.

**Parámetros**:
- `message`: Mensaje a enviar

Ver [tool_descriptions.md](tool_descriptions.md) para documentación detallada de cada herramienta.

---

## 📚 Documentación Adicional

- **[tool_descriptions.md](tool_descriptions.md)**: Descripción detallada de todas las herramientas del agente
- **[INSTRUCCIONES_DOCKER.md](INSTRUCCIONES_DOCKER.md)**: Guía completa de Docker
- **`prompts/`**: Plantillas de prompts usadas por el agente
- **API Docs**: http://localhost:8000/docs (cuando el servidor está corriendo)

---

## 🤝 Contribuciones

Este es un proyecto de trabajo final de máster. Para reportar issues o sugerencias, por favor contacta al autor.

---

## 📄 Licencia

Este proyecto es parte de un trabajo académico.

---

## 👤 Autor

Trabajo Final de Máster - FoodLooker
Agente Inteligente de Reservas con IA

---

## 🙏 Agradecimientos

- **LangChain/LangGraph**: Framework de agentes IA
- **OpenAI**: Modelos de lenguaje GPT
- **Google Cloud**: APIs de Maps, Places y Calendar
- **Twilio**: Servicio de llamadas telefónicas
- **ElevenLabs**: Text-to-speech de alta calidad
- **Streamlit**: Framework de interfaz web
