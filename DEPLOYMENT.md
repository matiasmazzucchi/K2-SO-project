# 🚀 Guía de Deployment en Google Cloud Run

Esta guía te ayudará a desplegar el bot K2-SO en Google Cloud Run.

## ✅ Requisitos Previos

1. **Proyecto Google Cloud creado**: `k2-proyect-491716`
2. **gcloud CLI instalado** y autenticado
3. **Docker instalado** (para tests locales, opcional)
4. **Service Account creada** con permisos a Firestore
5. **Credenciales configuradas** (ver sección más abajo)

## 📋 Paso 1: Configurar Credenciales

### 1.1 Crear Service Account en Google Cloud

```bash
# En Google Cloud Console:
1. Ir a "Cuentas de servicio"
2. Crear nueva cuenta de servicio
3. Nombre: k2-so-bot
4. Crear clave JSON
5. Descargar el archivo JSON
```

### 1.2 Configurar Permisos

La Service Account necesita estos roles:
- `Firestore Editor` (para leer/escribir en Firestore)
- `Cloud Logging Writer` (para logs)
- `Cloud Trace Writer` (para tracing, opcional)

## 🔐 Paso 2: Preparar Variables de Entorno en Cloud Run

En Google Cloud Console, ir a **Cloud Run** > **Variables de entorno**:

```
TELEGRAM_BOT_TOKEN=your_telegram_token
DEEPSEEK_API_KEY=your_deepseek_key
OPENAI_API_KEY=your_openai_key
PROJECT_ID=k2-proyect-491716
GOOGLE_APPLICATION_CREDENTIALS=/var/run/secrets/cloud.google.com/service_account/key.json
FIRESTORE_COLLECTION=conversations
DEFAULT_TIMEZONE=America/Argentina/Buenos_Aires
DEBUG=false
```

## 🐳 Paso 3: Construir y Subir Imagen Docker

### Opción A: Usando gcloud (RECOMENDADO)

```bash
# Desde la carpeta k2-migration
gcloud builds submit \
  --tag gcr.io/k2-proyect-491716/k2-so-bot:latest \
  --project=k2-proyect-491716

# Si prefieres una etiqueta con date
gcloud builds submit \
  --tag gcr.io/k2-proyect-491716/k2-so-bot:$(date +%Y%m%d-%H%M%S) \
  --project=k2-proyect-491716
```

### Opción B: Usando Docker localmente

```bash
# Construir imagen
docker build -t gcr.io/k2-proyect-491716/k2-so-bot:latest .

# Autenticar Docker
gcloud auth configure-docker

# Subir imagen
docker push gcr.io/k2-proyect-491716/k2-so-bot:latest
```

## 🚀 Paso 4: Desplegar en Cloud Run

### Opción A: Desde Cloud Console

1. Ir a **Cloud Run**
2. Click en **Crear Servicio**
3. Seleccionar imagen: `gcr.io/k2-proyect-491716/k2-so-bot:latest`
4. Nombre: `k2-so-bot`
5. Región: `us-central1` (o la que prefieras)
6. Permitir tráfico: `Todos`
7. Aumentar límites de recursos:
   - CPU: 2
   - Memoria: 1 GB
   - Timeout: 3600 segundos (1 hora)

### Opción B: Desde línea de comandos (gcloud CLI)

```bash
gcloud run deploy k2-so-bot \
  --image gcr.io/k2-proyect-491716/k2-so-bot:latest \
  --platform managed \
  --region us-central1 \
  --project k2-proyect-491716 \
  --memory 1Gi \
  --cpu 2 \
  --timeout 3600 \
  --set-env-vars "TELEGRAM_BOT_TOKEN=YOUR_TOKEN,DEEPSEEK_API_KEY=YOUR_KEY,OPENAI_API_KEY=YOUR_KEY,PROJECT_ID=k2-proyect-491716" \
  --allow-unauthenticated \
  --update-env-vars PORT=8080
```

## 🔗 Paso 5: Configurar Webhook de Telegram

Una vez desplegado, Cloud Run te dará una URL como:
```
https://k2-so-bot-XXXXX.a.run.app
```

Luego configura el webhook en Telegram:

```bash
# Reemplaza tu token y la URL
curl -F "url=https://k2-so-bot-XXXXX.a.run.app/webhook/telegram" \
  https://api.telegram.org/botYOUR_TOKEN/setWebhook
```

O desde Python:
```python
import requests

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
URL = "https://k2-so-bot-XXXXX.a.run.app/webhook/telegram"

requests.get(
    f"https://api.telegram.org/bot{TOKEN}/setWebhook",
    params={"url": URL}
)
```

## ✅ Paso 6: Verificar Deployment

### Revisar Health Check

```bash
# Reemplaza con tu URL
curl https://k2-so-bot-XXXXX.a.run.app/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "service": "K2-SO Bot",
  "version": "0.2.0"
}
```

### Ver Logs

```bash
gcloud run logs read k2-so-bot \
  --project k2-proyect-491716 \
  --limit 50
```

### Probar con mensaje

Manda un mensaje a tu bot de Telegram y verifica que responde.

## 🛠️ Pasos Adicionales

### Crear Service Account JSON

```bash
# Crear Service Account
gcloud iam service-accounts create k2-so-bot \
  --project=k2-proyect-491716 \
  --display-name="K2-SO Bot Service Account"

# Crear clave JSON
gcloud iam service-accounts keys create ./service-account.json \
  --iam-account=k2-so-bot@k2-proyect-491716.iam.gserviceaccount.com

# Otorgar permisos
gcloud projects add-iam-policy-binding k2-proyect-491716 \
  --member=serviceAccount:k2-so-bot@k2-proyect-491716.iam.gserviceaccount.com \
  --role=roles/datastore.user

gcloud projects add-iam-policy-binding k2-proyect-491716 \
  --member=serviceAccount:k2-so-bot@k2-proyect-491716.iam.gserviceaccount.com \
  --role=roles/logging.logWriter
```

### Crear Firestore Database

```bash
# En Google Cloud Console:
1. Ir a Firestore
2. Crear base de datos
3. Modo: Iniciar en modo seguro
4. Ubicación: us-central1
```

## 📊 Monitoreo

- **Cloud Logging**: Ver logs en tiempo real
- **Cloud Trace**: Rastrear llamadas
- **Cloud Monitoring**: Métricas de uso

## 🔄 Actualizaciones

Para actualizar el bot después de cambios:

```bash
# 1. Hacer commit en Git
git add .
git commit -m "Actualización de [describe cambios]"
git push

# 2. Reconstruir imagen
gcloud builds submit \
  --tag gcr.io/k2-proyect-491716/k2-so-bot:latest \
  --project=k2-proyect-491716

# 3. Redeploy (auto o manual en Cloud Console)
```

## 🐛 Troubleshooting

### Error: "Permission denied"
- Verifica que la Service Account tenga permisos
- Revisa que GOOGLE_APPLICATION_CREDENTIALS esté configurado

### Error: "Webhook invalid"
- Verifica la URL sea HTTPS
- Confirma que `/health` retorna 200
- Revisa que el token sea correcto

### Bot no responde
- Revisa los logs: `gcloud run logs read k2-so-bot`
- Verifica variables de entorno
- Confirma que el Usuario está autorizado (ID: 8071121316)

## 🆘 Contacto

Para errores, revisa:
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Google Cloud Support](https://cloud.google.com/support)

---

**Última actualización:** Abril 6, 2026
