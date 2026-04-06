# 📋 Instrucciones para Salir a Producción - K2-SO Bot

**Estado Actual:** ✅ Bot funciona localmente | ⏳ Falta: Cloud Run + APIs configuradas

**Objetivo:** Tener el bot en producción recibiendo mensajes en Telegram y agendando gastos automáticamente

---

## 🎯 Pasos Pendientes para Producción

### **FASE 1: Preparar Google Cloud (15 minutos)** 

#### 1.1 Crear Service Account
```bash
# En Google Cloud Console o terminal:
gcloud iam service-accounts create k2-so-bot \
  --project=k2-proyect-491716 \
  --display-name="K2-SO Bot Service Account"

# Crear clave JSON
gcloud iam service-accounts keys create ./k2-so-bot-key.json \
  --iam-account=k2-so-bot@k2-proyect-491716.iam.gserviceaccount.com

# ⚠️ GUARDAR ESTE ARCHIVO EN LUGAR SEGURO (NO COMMITTEAR A GIT)
```

#### 1.2 Otorgar Permisos
```bash
# Firestore
gcloud projects add-iam-policy-binding k2-proyect-491716 \
  --member=serviceAccount:k2-so-bot@k2-proyect-491716.iam.gserviceaccount.com \
  --role=roles/datastore.user

# Cloud Logging
gcloud projects add-iam-policy-binding k2-proyect-491716 \
  --member=serviceAccount:k2-so-bot@k2-proyect-491716.iam.gserviceaccount.com \
  --role=roles/logging.logWriter

# Cloud Run
gcloud projects add-iam-policy-binding k2-proyect-491716 \
  --member=serviceAccount:k2-so-bot@k2-proyect-491716.iam.gserviceaccount.com \
  --role=roles/run.serviceAgent
```

#### 1.3 Crear Firestore Database
```bash
# En Google Cloud Console:
1. Ir a Firestore
2. "Crear base de datos"
3. Modo: "Iniciar en modo seguro"
4. Ubicación: "us-central1"
5. Crear
```

#### 1.4 Habilitar APIs Necesarias
```bash
gcloud services enable \
  firestore.googleapis.com \
  run.googleapis.com \
  container.googleapis.com \
  cloudbuild.googleapis.com \
  --project=k2-proyect-491716
```

---

### **FASE 2: Crear Secretos en Google Cloud (10 minutos)**

```bash
# ⚠️ IMPORTANTE: Guardar tus API keys en archivo .env local (NO EN GIT)
# Usar los valores de tu .env local

# Crear secretos con tus valores reales
gcloud secrets create TELEGRAM_BOT_TOKEN \
  --data-file=- \
  --project=k2-proyect-491716 \
  <<< "TU_TELEGRAM_BOT_TOKEN_AQUI"

gcloud secrets create DEEPSEEK_API_KEY \
  --data-file=- \
  --project=k2-proyect-491716 \
  <<< "TU_DEEPSEEK_API_KEY_AQUI"

gcloud secrets create OPENAI_API_KEY \
  --data-file=- \
  --project=k2-proyect-491716 \
  <<< "TU_OPENAI_API_KEY_AQUI"

# Dar permisos al servicio service account
gcloud secrets add-iam-policy-binding TELEGRAM_BOT_TOKEN \
  --member=serviceAccount:k2-so-bot@k2-proyect-491716.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor \
  --project=k2-proyect-491716

# (Repetir para DEEPSEEK_API_KEY y OPENAI_API_KEY)
gcloud secrets add-iam-policy-binding DEEPSEEK_API_KEY \
  --member=serviceAccount:k2-so-bot@k2-proyect-491716.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor \
  --project=k2-proyect-491716

gcloud secrets add-iam-policy-binding OPENAI_API_KEY \
  --member=serviceAccount:k2-so-bot@k2-proyect-491716.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor \
  --project=k2-proyect-491716
```

---

### **FASE 3: Build y Deploy a Cloud Run (15 minutos)**

#### 3.1 Compilar Docker Image
```bash
cd c:\Users\matia\OneDrive\Escritorio\claude_code_testing\k2-migration

# Opción A: Usar gcloud builds (RECOMENDADO)
gcloud builds submit \
  --tag gcr.io/k2-proyect-491716/k2-so-bot:v1 \
  --project=k2-proyect-491716

# Esperar a que termine (5-10 minutos)
# Ver progreso: gcloud builds log --stream
```

#### 3.2 Deploy a Cloud Run
```bash
gcloud run deploy k2-so-bot \
  --image gcr.io/k2-proyect-491716/k2-so-bot:v1 \
  --platform managed \
  --region us-central1 \
  --project k2-proyect-491716 \
  --memory 1Gi \
  --cpu 2 \
  --timeout 3600 \
  --service-account k2-so-bot@k2-proyect-491716.iam.gserviceaccount.com \
  --allow-unauthenticated \
  --set-env-vars PORT=8080 \
  --update-secrets "TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest" \
  --update-secrets "DEEPSEEK_API_KEY=DEEPSEEK_API_KEY:latest" \
  --update-secrets "OPENAI_API_KEY=OPENAI_API_KEY:latest"
```

**Resultado:** Te dará una URL como:
```
https://k2-so-bot-xxxxx.a.run.app
```

#### 3.3 Verificar que está operativo
```bash
# Test de health check
curl https://k2-so-bot-xxxxx.a.run.app/health

# Deberías ver:
# {"status":"healthy","service":"K2-SO Bot","version":"0.2.0"}
```

---

### **FASE 4: Configurar Webhook de Telegram (5 minutos)**

Una vez tengas la URL de Cloud Run:

```bash
# Variables
$CLOUD_RUN_URL = "https://k2-so-bot-xxxxx.a.run.app"
$TOKEN = "TU_TOKEN_TELEGRAM_AQUI"  # De tu .env local
$WEBHOOK_URL = "$CLOUD_RUN_URL/webhook/telegram"

# Opción A: Desde PowerShell
Invoke-WebRequest -Uri "https://api.telegram.org/bot$TOKEN/setWebhook" `
  -Method Post `
  -Body @{url = $WEBHOOK_URL} | ConvertTo-Json

# Opción B: Desde bash/curl
curl -X POST -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "url=$WEBHOOK_URL" \
  "https://api.telegram.org/bot$TOKEN/setWebhook"
```

**Verificar que funcionó:**
```bash
curl "https://api.telegram.org/bot$TOKEN/getWebhookInfo"

# Deberías ver tu URL configurada
```

---

### **FASE 5: Prueba End-to-End (5 minutos)**

1. **Abre Telegram**
2. **Manda mensaje a tu bot**: "Gasta 100 en comida"
3. **El bot debería responder** (aunque sea dummy por ahora)
4. **Revisar logs** en Cloud Run:
   ```bash
   gcloud run logs read k2-so-bot \
     --limit 50 \
     --project k2-proyect-491716
   ```

---

### **FASE 6: Completar Funcionalidad de Agendado de Gastos** ⏳

**Lo que FALTA para que funcione el agendado completo:**

1. ✅ **Agente Financiero** - Ya existe
2. ❌ **Conexión a Google Sheets** - Necesita OAuth/Service Account
3. ❌ **Memory Manager** - Firestore integration completa
4. ❌ **Message Router** - Completar lógica de routing
5. ❌ **LangChain Agent Executor** - Setup completo con tool calling

---

## ⚠️ Checklist de Producción

- [ ] Google Cloud project configurado
- [ ] Service Account creada
- [ ] Firestore database activa
- [ ] Secretos en Secret Manager
- [ ] Docker image buildeada
- [ ] Cloud Run service deployado
- [ ] Webhook de Telegram configurado
- [ ] Health check `/health` respondiendo
- [ ] Firestore Memory implementado ⏳
- [ ] Google Sheets conectado ⏳
- [ ] Prueba: Agendado de gasto funciona ⏳
- [ ] Logs en Cloud Logging
- [ ] Monitoreo activo

---

## 🚀 Resumen Rápido de Comandos

### Setup Google Cloud
```bash
# 1. Service Account
gcloud iam service-accounts create k2-so-bot \
  --project=k2-proyect-491716
gcloud iam service-accounts keys create ./k2-so-bot-key.json \
  --iam-account=k2-so-bot@k2-proyect-491716.iam.gserviceaccount.com

# 2. Permisos
gcloud projects add-iam-policy-binding k2-proyect-491716 \
  --member=serviceAccount:k2-so-bot@k2-proyect-491716.iam.gserviceaccount.com \
  --role=roles/datastore.user

# 3. APIs
gcloud services enable firestore.googleapis.com run.googleapis.com cloudbuild.googleapis.com \
  --project=k2-proyect-491716
```

### Build & Deploy
```bash
# 1. Build
gcloud builds submit \
  --tag gcr.io/k2-proyect-491716/k2-so-bot:v1 \
  --project=k2-proyect-491716

# 2. Deploy
gcloud run deploy k2-so-bot \
  --image gcr.io/k2-proyect-491716/k2-so-bot:v1 \
  --platform managed \
  --region us-central1 \
  --memory 1Gi \
  --cpu 2 \
  --allow-unauthenticated
```

### Logs & Debugging
```bash
# Ver logs
gcloud run logs read k2-so-bot --project k2-proyect-491716

# Ver webhook status
curl "https://api.telegram.org/bot$TOKEN/getWebhookInfo"

# Health check
curl https://k2-so-bot-xxxxx.a.run.app/health
```

---

## 🤖 Siguiente Paso

Para completar la funcionalidad 100% necesitamos un **agente Copilot** que implemente:

1. **FirestoreMemory** - Guardar/cargar conversaciones
2. **Google Sheets API** - Conectar para agendado de gastos
3. **MessageRouter completo** - Routing inteligente de mensajes
4. **LangChain Agent** - Tool calling agent funcional
5. **Tests e2e** - Validar flujo completo

**¿Deseas que lancemos un agente ahora para completar esto?** 🚀

---

## 📞 Troubleshooting

| Error | Solución |
|-------|----------|
| `503 Service Unavailable` | Esperar a que Cloud Run termine de iniciar (2-3 min) |
| `403 Permission Denied` | Revisar Service Account tiene roles correctos |
| `Webhook invalid` | Verificar URL es HTTPS y health check retorna 200 |
| `Import Error` | Revisar instalar todas las dependencias: `pip install -r requirements.txt` |
| `Firestore error` | Verificar database está creada en modo seguro |

---

**Versión:** 1.0 | **Actualizado:** Abril 6, 2026
