"""
===========================================================
CALENDAR TOOLS - Integración con Google Calendar
===========================================================

Usa langchain_google_community.CalendarToolkit para gestionar
el calendario del usuario.

Configuración:
1. Descarga credentials.json de Google Cloud Console
2. Colócalo en la raíz del proyecto
3. La primera ejecución abrirá el navegador para autorizar
4. Se generará token.json automáticamente

Requiere:
- pip install langchain-google-community
"""

import os
from typing import List, Any
from dotenv import load_dotenv

from langchain_google_community import CalendarToolkit

load_dotenv()

# ===========================================================
# CONFIGURACIÓN
# ===========================================================

CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")

# Cache de herramientas
_calendar_tools: List[Any] = []
_initialized = False


def is_calendar_configured() -> bool:
    """Verifica si Google Calendar está configurado (existe credentials.json)."""
    return os.path.exists(CREDENTIALS_PATH)


def init_calendar() -> List[Any]:
    """
    Inicializa y devuelve las herramientas de Google Calendar.
    
    Usa CalendarToolkit de langchain-google-community que proporciona:
    - create_calendar_event: Crear eventos
    - get_calendar_events: Listar eventos
    - update_calendar_event: Modificar eventos
    - delete_calendar_event: Eliminar eventos
    - search_calendar_events: Buscar eventos
    
    Returns:
        Lista de herramientas de calendario
    """
    global _calendar_tools, _initialized
    
    # Si ya se inicializó, devolver cache
    if _initialized:
        return _calendar_tools
    
    # Verificar configuración
    if not is_calendar_configured():
        print(f"⚠️  Google Calendar no configurado (falta {CREDENTIALS_PATH})")
        _initialized = True
        return []
    
    try:
        # Importar CalendarToolkit
        
        # Configurar paths en variables de entorno si son personalizados
        if CREDENTIALS_PATH != "credentials.json":
            os.environ["GOOGLE_CALENDAR_CREDENTIALS_PATH"] = CREDENTIALS_PATH
        if TOKEN_PATH != "token.json":
            os.environ["GOOGLE_CALENDAR_TOKEN_PATH"] = TOKEN_PATH
        
        print("🔄 Inicializando Google Calendar...")
        
        # Crear toolkit (esto puede abrir el navegador la primera vez)
        toolkit = CalendarToolkit()
        
        # Obtener herramientas
        tools = toolkit.get_tools()
        
        if tools:
            print(f"✅ Google Calendar habilitado ({len(tools)} herramientas):")
            for tool in tools:
                print(f"   - {tool.name}")
            _calendar_tools = tools
        else:
            print("⚠️  CalendarToolkit no devolvió herramientas")
        
        _initialized = True
        return _calendar_tools
        
    except ImportError as e:
        print("⚠️  langchain-google-community no instalado")
        print("   Instala con: pip install langchain-google-community")
        _initialized = True
        return []
        
    except Exception as e:
        print(f"⚠️  Error inicializando Google Calendar: {e}")
        _initialized = True
        return []


def get_calendar_tools() -> List[Any]:
    """
    Obtiene las herramientas de calendario (inicializa si es necesario).
    
    Returns:
        Lista de herramientas de calendario
    """
    if not _initialized:
        return init_calendar()
    return _calendar_tools