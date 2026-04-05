# Plan de Migración: K2-SO Bot → Google Cloud

**Proyecto ID:** `k2-proyect-491716`
**Fecha:** 2026-03-29

---

## 📊 ANÁLISIS ACTUAL

### Arquitectura N8N Existente

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Telegram Webhook Trigger                            │
│                              (bot token)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Switch1: Autorización                                │
│                    Usuarios: Matias, Hector                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Switch4: Tipo de Mensaje                             │
│              ┌─────────┬─────────┬─────────┬─────────┐                      │
│              │  Texto  │  Audio  │  Foto   │   PDF   │                      │
│              └─────────┴─────────┴─────────┴─────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
        │              │              │              │
        ▼              ▼              ▼              ▼
    ┌───────┐    ┌──────────┐   ┌───────────┐  ┌─────────────┐
    │ Direct│    │ Whisper  │   │ GPT-4o    │  │ PDF Extract  │
    │ Input │    │Transcribe│   │ Vision    │  │              │
    └───────┘    └──────────┘   └───────────┘  └─────────────┘
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI Agent Principal (DeepSeek)                        │
│                    Personalidad: K2 (droide imperial)                       │
│                    Memoria: Buffer 10 mensajes                               │
│                    ┌─────────────────────────────────────────┐              │
│                    │         Tools (Sub-Agentes)              │              │
│                    │  ┌─────────────────────────────────────┐│              │
│                    │  │ Agente Financiero                   ││              │
│                    │  │  - ver_egresos                      ││              │
│                    │  │  - ver_egresos_fijos                ││              │
│                    │  │  - Categorias de egresos            ││              │
│                    │  │  - Nuevo Egreso                     ││              │
│                    │  └─────────────────────────────────────┘│              │
│                    │  ┌─────────────────────────────────────┐│              │
│                    │  │ Agente Calendario                   ││              │
│                    │  │  - Get events                       ││              │
│                    │  │  - Create event                     ││              │
│                    │  │  - Update event                     ││              │
│                    │  │  - Delete event                     ││              │
│                    │  └─────────────────────────────────────┘│              │
│                    │  ┌─────────────────────────────────────┐│              │
│                    │  │ Agente Nutricional                  ││              │
│                    │  │  - Análisis de imágenes             ││              │
│                    │  └─────────────────────────────────────┘│              │
│                    │  ┌─────────────────────────────────────┐│              │
│                    │  │ Agente Supermercado                 ││              │
│                    │  │  - Ver comparativa precios          ││              │
│                    │  │  - Agregar producto                 ││              │
│                    │  └─────────────────────────────────────┘│              │
│                    └─────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Switch5: Respuesta                                   │
│              ┌─────────┬─────────┬─────────┐                                │
│              │  Texto  │  Audio  │  Foto   │                                │
│              └─────────┴─────────┴─────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘
        │              │              │
        ▼              ▼              ▼
    ┌───────┐    ┌──────────┐   ┌───────────┐
    │ Text  │    │OpenAI TTS│   │   Text    │
    │ Reply │    │ + Audio  │   │   Reply   │
    └───────┘    └──────────┘   └───────────┘
```

### Credenciales y APIs Actuales
| Servicio | Credencial | Uso |
|----------|------------|-----|
| Telegram | Bot Guias Locales Operativo | Webhook + Mensajería |
| OpenAI | TESTING ACOUNT | Whisper, GPT-4o, TTS |
| DeepSeek | DeepSeek account | LLM Principal |
| Google Sheets | Google Sheets OAuth2 | Datos financieros |
| Google Calendar | Google Calendar OAuth2 | Gestión de eventos |

---

## 🔄 PROPUESTA DE MIGRACIÓN

### Arquitectura Propuesta para Google Cloud

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Google Cloud Platform                                │
│                        Project: k2-proyect-491716                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         CAPA DE ENTRADA                                      │
│  ┌─────────────────────┐    ┌─────────────────────────────────────────────┐│
│  │   Telegram Webhook  │    │          Cloud Load Balancer                ││
│  │   (HTTPS POST)      │───▶│          (SSL Termination)                  ││
│  └─────────────────────┘    └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CAPA DE APLICACIÓN                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    Cloud Run (Container)                                ││
│  │                                                                         ││
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐    ││
│  │  │  Bot Handler   │  │  Auth Service  │  │  Session Manager        │    ││
│  │  │  (FastAPI)      │  │  (User Filter) │  │  (Firestore Client)    │    ││
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘    ││
│  │                                                                         ││
│  │  ┌────────────────────────────────────────────────────────────────┐   ││
│  │  │              Agent Orchestrator (LangGraph/LangChain)            │   ││
│  │  │                                                                  │   ││
│  │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────┐ │   ││
│  │  │  │  Financial   │ │  Calendar    │ │  Nutrition   │ │ Shopping│ │   ││
│  │  │  │  Agent       │ │  Agent       │ │  Agent       │ │ Agent   │ │   ││
│  │  │  └──────────────┘ └──────────────┘ └──────────────┘ └─────────┘ │   ││
│  │  └────────────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CAPA DE DATOS                                        │
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │   Firestore         │  │   Cloud Storage     │  │   Secret Manager    │  │
│  │   - Sessions        │  │   - Temp files      │  │   - API Keys        │  │
│  │   - User Data       │  │   - Uploaded files  │  │   - OAuth tokens    │  │
│  │   - Memory Context  │  │   - Audio cache     │  │   - Credentials     │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CAPA DE INTEGRACIÓN                                  │
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │   Vertex AI        │  │   Google Sheets     │  │   Google Calendar   │  │
│  │   (Gemini/DeepSeek)│  │   API               │  │   API               │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐                           │
│  │   Cloud Functions   │  │   Cloud Tasks       │                           │
│  │   (Background)      │  │   (Async Queue)     │                           │
│  └─────────────────────┘  └─────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📝 COMPONENTES A IMPLEMENTAR

### Fase 1: Infraestructura Base

#### 1.1 Cloud Run Service Principal
```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: k2-bot-service
  project: k2-proyect-491716
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        autoscaling.knative.dev/minScale: "1"
    spec:
      containers:
      - image: gcr.io/k2-proyect-491716/k2-bot:latest
        env:
        - name: PROJECT_ID
          value: k2-proyect-491716
        - name: TELEGRAM_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: telegram-credentials
              key: bot-token
        resources:
          limits:
            memory: "1Gi"
            cpu: "2"
        ports:
        - containerPort: 8080
```

#### 1.2 Estructura del Proyecto Python
```
k2-bot/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py           # Configuración centralizada
│   │   └── prompts.py            # Prompts del sistema K2
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # Agente principal
│   │   ├── financial.py          # Agente financiero
│   │   ├── calendar.py           # Agente calendario
│   │   ├── nutrition.py          # Agente nutricional
│   │   └── shopping.py           # Agente supermercado
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── telegram.py           # Webhook handler
│   │   ├── message_router.py     # Router por tipo
│   │   └── response.py           # Generador de respuestas
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── sheets_tool.py        # Google Sheets operations
│   │   ├── calendar_tool.py      # Google Calendar operations
│   │   ├── vision_tool.py        # Image analysis
│   │   └── transcription_tool.py # Whisper transcription
│   ├── memory/
│   │   ├── __init__.py
│   │   └── firestore_memory.py   # Persistencia de memoria
│   ├── auth/
│   │   ├── __init__.py
│   │   └── user_filter.py        # Filtro de usuarios autorizados
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── tests/
├── Dockerfile
├── requirements.txt
├── cloudbuild.yaml
└── README.md
```

### Fase 2: Migración de Funcionalidades

#### 2.1 Mapeo de Nodos N8N → Código Python

| Nodo N8N | Implementación Python |
|----------|----------------------|
| Telegram Trigger | FastAPI endpoint `/webhook/telegram` |
| Switch1 (Auth) | `auth/user_filter.py` - validate_user() |
| Switch4 (Type Router) | `handlers/message_router.py` - route_message() |
| AI Agent3 | `agents/orchestrator.py` - K2Agent class |
| Simple Memory3 | `memory/firestore_memory.py` - SessionMemory |
| DeepSeek Chat Model | Vertex AI / DeepSeek API client |
| Agente Financiero | `agents/financial.py` - FinancialAgent |
| Agente Calendario | `agents/calendar.py` - CalendarAgent |
| Agente Nutricional | `agents/nutrition.py` - NutritionAgent |
| Precios Supermercado | `agents/shopping.py` - ShoppingAgent |
| Google Sheets Tools | `tools/sheets_tool.py` |
| Google Calendar Tools | `tools/calendar_tool.py` |
| OpenAI Whisper | `tools/transcription_tool.py` |
| GPT-4o Vision | `tools/vision_tool.py` |
| OpenAI TTS | `handlers/response.py` - generate_audio_response() |

#### 2.2 Implementación del Agente Principal

```python
# src/agents/orchestrator.py
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from google.cloud import firestore
from datetime import datetime
import pytz

from ..config.prompts import K2_SYSTEM_PROMPT
from ..tools.sheets_tool import SheetsToolkit
from ..tools.calendar_tool import CalendarToolkit
from .financial import FinancialAgent
from .calendar import CalendarAgent
from .nutrition import NutritionAgent
from .shopping import ShoppingAgent

class K2Orchestrator:
    """
    Agente principal K2-SO que coordina todos los sub-agentes.
    Personalidad: Droide imperial sarcástico.
    """

    def __init__(self, project_id: str, user_id: str):
        self.project_id = project_id
        self.user_id = user_id
        self.db = firestore.Client(project=project_id)
        self.memory = self._load_conversation_memory()

        # Inicializar sub-agentes
        self.financial_agent = FinancialAgent(project_id)
        self.calendar_agent = CalendarAgent(project_id)
        self.nutrition_agent = NutritionAgent()
        self.shopping_agent = ShoppingAgent(project_id)

        # Configurar LLM principal
        self.llm = self._configure_llm()

    def _configure_llm(self):
        """Configura el modelo de lenguaje principal."""
        from langchain_deepseek import ChatDeepSeek
        return ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.7
        )

    def _load_conversation_memory(self) -> list:
        """Carga el historial de conversación desde Firestore."""
        doc_ref = self.db.collection("conversations").document(self.user_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return data.get("messages", [])[-10:]  # Últimos 10 mensajes
        return []

    def save_memory(self):
        """Guarda la memoria de conversación en Firestore."""
        doc_ref = self.db.collection("conversations").document(self.user_id)
        doc_ref.set({
            "messages": self.memory,
            "last_updated": datetime.now(pytz.timezone("America/Argentina/Buenos_A Aires"))
        }, merge=True)

    async def process_message(self, user_input: str, context: dict = None) -> str:
        """
        Procesa un mensaje del usuario y devuelve la respuesta de K2.

        Args:
            user_input: Texto o instrucción del usuario
            context: Contexto adicional (imagen, audio transcrito, etc.)

        Returns:
            Respuesta del agente K2
        """
        # Determinar qué agente debe manejar la solicitud
        # basándose en el contenido del mensaje
        pass
```

### Fase 3: Servicios de Google Cloud

#### 3.1 Configuración de Secret Manager
```bash
# Crear secrets para las credenciales
gcloud secrets create telegram-bot-token --replication-policy="automatic"
gcloud secrets create deepseek-api-key --replication-policy="automatic"
gcloud secrets create openai-api-key --replication-policy="automatic"
gcloud secrets create google-oauth-credentials --replication-policy="automatic"

# Añadir valores
echo -n "TU_TOKEN_TELEGRAM" | gcloud secrets versions add telegram-bot-token --data-file=-
echo -n "TU_DEEPSEEK_KEY" | gcloud secrets versions add deepseek-api-key --data-file=-
```

#### 3.2 Firestore Collections Structure
```javascript
// collections structure

// users - Datos de usuario y preferencias
{
  "users": {
    "8071121316": {
      "name": "Matias",
      "authorized": true,
      "preferences": {
        "timezone": "America/Argentina/Buenos_Aires",
        "language": "es-AR"
      },
      "created_at": "2025-01-01T00:00:00Z"
    }
  }
}

// conversations - Memoria de conversaciones
{
  "conversations": {
    "8071121316": {
      "messages": [
        {
          "role": "user",
          "content": "¿Cuánto gasté ayer?",
          "timestamp": "2025-03-29T10:00:00Z"
        },
        {
          "role": "assistant",
          "content": "Según mis registros...",
          "timestamp": "2025-03-29T10:00:05Z"
        }
      ],
      "last_updated": "2025-03-29T10:00:05Z"
    }
  }
}

// expenses - Egresos (sincronizado con Sheets)
{
  "expenses": {
    "auto_id": {
      "user_id": "8071121316",
      "category": "alimentacion",
      "amount": 1500,
      "description": "Supermercado",
      "date": "2025-03-29",
      "synced_to_sheets": true
    }
  }
}
```

#### 3.3 Cloud Functions para Procesamiento Asíncrono
```python
# functions/process_audio/main.py
import functions_framework
from google.cloud import storage
import openai
import os

@functions_framework.http
def process_audio(request):
    """
    Procesa archivos de audio de forma asíncrona.
    Trigger: Cloud Storage upload
    """
    file_url = request.json.get('file_url')

    # Descargar archivo
    # Transcribir con Whisper
    # Guardar resultado en Firestore
    # Notificar al usuario via Telegram

    return {"status": "processed", "text": transcription}
```

---

## ⚠️ CONSIDERACIONES DE MIGRACIÓN

### Riesgos Identificados

| Riesgo | Mitigación |
|--------|------------|
| Pérdida de datos de sesiones activas | Migrar memoria gradualmente, mantener N8N activo durante transición |
| Latencia en respuestas | Cloud Run con min_instances=1 para cold starts |
| OAuth tokens de Google | Implementar refresh tokens con Secret Manager |
| Dependencia de DeepSeek | Configurar fallback a Vertex AI Gemini |

### Dependencias Externas

1. **Telegram Bot API** - Token actual en N8N
2. **DeepSeek API** - Modelo principal de lenguaje
3. **OpenAI API** - Whisper, GPT-4o Vision, TTS
4. **Google Sheets API** - Datos financieros
5. **Google Calendar API** - Gestión de eventos

---

## 🚀 PLAN DE IMPLEMENTACIÓN

### Paso 1: Setup del Proyecto GCP
```bash
# Configurar proyecto
gcloud config set project k2-proyect-491716

# Habilitar APIs necesarias
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### Paso 2: Crear Infraestructura
- [ ] Crear bucket de Cloud Storage para archivos temporales
- [ ] Configurar base de datos Firestore
- [ ] Crear secrets en Secret Manager
- [ ] Configurar OAuth 2.0 para Google Sheets y Calendar

### Paso 3: Implementar Backend
- [ ] Crear estructura del proyecto Python
- [ ] Implementar FastAPI con endpoint de webhook
- [ ] Migrar lógica de autorización de usuarios
- [ ] Implementar router de tipos de mensaje

### Paso 4: Migrar Agentes
- [ ] Agente Principal K2 con DeepSeek
- [ ] Agente Financiero con Google Sheets
- [ ] Agente Calendario con Google Calendar
- [ ] Agente Nutricional con GPT-4o Vision
- [ ] Agente Supermercado

### Paso 5: Migrar Memoria
- [ ] Implementar persistencia en Firestore
- [ ] Migrar datos históricos de sesiones

### Paso 6: Testing y Validación
- [ ] Tests unitarios por componente
- [ ] Tests de integración end-to-end
- [ ] Validación con usuarios autorizados

### Paso 7: Despliegue Gradual
- [ ] Desplegar versión beta en Cloud Run
- [ ] Configurar webhook de Telegram para apuntar al nuevo endpoint
- [ ] Monitorear métricas y errores
- [ ] Migrar tráfico gradualmente (canary deployment)

---

## 📊 ESTIMACIÓN DE COSTOS GCP

| Servicio | Uso Estimado | Costo Mensual |
|----------|-------------|----------------|
| Cloud Run | 100k requests/mes | ~$10-20 |
| Firestore | 1GB storage + 500k ops | ~$20 |
| Secret Manager | 5 secrets | ~$5 |
| Cloud Storage | 10GB | ~$2 |
| Vertex AI (fallback) | Variable | ~$20-50 |
| DeepSeek API | Variable | ~$10-30 |
| OpenAI API | Whisper + Vision + TTS | ~$15-40 |
| **Total Estimado** | | **~$80-170/mes** |

---

## 🔗 PRÓXIMOS PASOS

1. **Confirmar preferencias de migración** - ¿Quieres mantener DeepSeek como LLM principal o migrar a Vertex AI Gemini?
2. **Configurar OAuth** - Necesitamos configurar las credenciales OAuth para Google Sheets y Calendar
3. **Definir cronograma** - ¿Cuándo quieres iniciar la migración?
4. **Nuevas funcionalidades** - ¿Qué herramientas adicionales quieres integrar?