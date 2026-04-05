# K2-SO Project

**K2-SO** es un asistente de IA tipo droide imperial que migra desde N8N a Python con LangChain, permitiendo gestión inteligente de tareas domésticas y profesionales.

## 🤖 Descripción

K2-SO es un bot de Telegram inteligente que funciona como asistente personal. Utiliza DeepSeek como LLM principal y coordina múltiples sub-agentes especializados para diferentes funcionalidades.

**Personalidad:** Droide imperial sarcástico, asistente para tareas de gestión y domésticas. Se refiere al usuario como "Matz".

## 🎯 Funcionalidades Actuales

### Sub-Agentes Disponibles

#### 1. **Agente Financiero** 💰
- Ver egresos registrados (variables y fijos)
- Registrar nuevos gastos con categorización automática
- Consultar categorías de egresos
- Integración con Google Sheets

#### 2. **Agente Calendario** 📅
- Crear eventos (duración por defecto: 30 min)
- Consultar próximos eventos
- Actualizar eventos existentes
- Eliminar eventos
- Integración con Google Calendar

#### 3. **Agente Nutricional** 🥗
- Análisis de imágenes de comida
- Identificación de alimentos
- Estimación de calorías
- Información nutricional detallada
- Integración con GPT-4o Vision

#### 4. **Agente de Correo** 📧 *(NUEVO)*
- Lectura de emails sin leer
- Búsqueda de emails por términos
- Listado de emails por contacto
- Solo lectura (sin permisos de envío/eliminación)
- Integración con Gmail API

## 🛠️ Stack Tecnológico

- **Backend:** Python 3.10+
- **LLM Principal:** DeepSeek (vía langchain)
- **Framework:** LangChain
- **Base de Datos:** Firestore (Google Cloud)
- **APIs Externas:**
  - Gmail API (lectura)
  - Google Sheets API
  - Google Calendar API
  - OpenAI (visión para agente nutricional)
  - Telegram Bot API
- **Orquestación:** Google Cloud Run (próximamente)
- **Cloud:** Google Cloud Platform (k2-proyect-491716)

## 📦 Estructura del Proyecto

```
k2-migration/
├── k2-bot/
│   ├── src/
│   │   ├── agents/          # Sub-agentes especializados
│   │   │   ├── calendar.py
│   │   │   ├── email.py          # NUEVO
│   │   │   ├── financial.py
│   │   │   ├── nutrition.py
│   │   │   ├── shopping.py
│   │   │   ├── orchestrator.py   # Coordinador principal
│   │   │   └── __init__.py
│   │   ├── config/          # Configuración centralizada
│   │   │   ├── settings.py
│   │   │   ├── prompts.py
│   │   │   └── __init__.py
│   │   ├── tools/           # Clientes de APIs externas
│   │   │   ├── gmail_tool.py     # NUEVO
│   │   │   ├── sheets_tool.py
│   │   │   └── calendar_tool.py
│   │   ├── handlers/        # Manejadores de eventos
│   │   ├── memory/          # Gestión de memoria
│   │   └── auth/            # Autenticación y autorización
│   └── tests/
├── PLAN_DE_MIGRACION.md     # Documentación técnica
├── GMAIL_SETUP.md           # Guía de configuración de Gmail
└── .gitignore
```

## 🚀 Instalación y Setup

### Requisitos Previos
- Python 3.10+
- Google Cloud Project configurado
- Cuenta de Telegram Bot
- Credenciales de Google (Sheets, Calendar, Gmail)

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/matiasmazzucchi/K2-SO-project.git
   cd K2-SO-project/k2-migration
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus credenciales
   ```

5. **Configurar Gmail** (ver [GMAIL_SETUP.md](GMAIL_SETUP.md))

6. **Ejecutar el bot**
   ```bash
   python -m k2_bot
   ```

## 🔐 Seguridad

### Usuarios Autorizados
- **Matías (ID: 8071121316)** ✅

### Permisos de Gmail
- ✅ Solo lectura (SCOPES: gmail.readonly)
- ❌ No puede enviar emails
- ❌ No puede eliminar emails
- ❌ No puede modificar emails

### Almacenamiento de Credenciales
- Credenciales en `GOOGLE_APPLICATION_CREDENTIALS`
- Tokens de OAuth locales en `token.json`
- Nunca se almacenan en el repositorio

## 📝 Variables de Entorno Requeridas

```env
# Google Cloud
PROJECT_ID=k2-proyect-491716

# Telegram
TELEGRAM_BOT_TOKEN=your_token_here

# APIs de LLM
DEEPSEEK_API_KEY=your_key
OPENAI_API_KEY=your_key

# OAuth Google
GOOGLE_CLIENT_ID=your_id
GOOGLE_CLIENT_SECRET=your_secret
GOOGLE_REFRESH_TOKEN=your_token

# Gmail
GMAIL_CREDENTIALS_PATH=path/to/credentials.json
GMAIL_TOKEN_PATH=token.json

# Base de datos
FIRESTORE_COLLECTION=conversations
DEFAULT_TIMEZONE=America/Argentina/Buenos_Aires
```

## 🔄 Cambios Recientes (v0.2.0)

### Nuevas Funcionalidades
- ✅ **Agente de Email** - Lectura de Gmail integrada
- ✅ **Autorización mejorada** - Solo Matías como usuario autorizado
- ✅ Removido agente de supermercado

### Mejoras
- Estructura de código mejorada
- Mejor separación de responsabilidades
- Documentación de Gmail setup

### Bugs Corregidos
- N/A

## 📚 Documentación

- [PLAN_DE_MIGRACION.md](./PLAN_DE_MIGRACION.md) - Arquitectura técnica y propuesta de migración
- [GMAIL_SETUP.md](./GMAIL_SETUP.md) - Configuración de integración de Gmail

## 🤝 Contribuciones

Este es un proyecto personal en desarrollo. Las contribuciones se realizan mediante pull requests en esta rama principal.

## 📋 Roadmap

### Próximas Features
- [ ] Integración con WhatsApp
- [ ] Dashboard web
- [ ] Análisis de gastos más avanzados
- [ ] Recomendaciones inteligentes
- [ ] Alertas automáticas
- [ ] Exportación de reportes

### En Consideración
- [ ] Integración con bases de datos de alimentos
- [ ] API pública para terceros
- [ ] Interfaz de voz

## 📄 Licencia

MIT License - Proyecto personal

## 👤 Autor

**Matías Mazzucchi**
- GitHub: [@matiasmazzucchi](https://github.com/matiasmazzucchi)
- Email: matiasmazzucchi@gmail.com

## 🐛 Reporte de Bugs

Para reportar bugs, abre un issue en el repositorio con:
- Descripción clara del problema
- Pasos para reproducirlo
- Comportamiento esperado vs actual

---

**Última actualización:** Abril 5, 2026
