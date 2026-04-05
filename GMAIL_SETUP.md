# Configuración de Gmail para K2-SO

## ¿Qué necesitas hacer?

El agente de email de K2 ha sido configurado para conectarse a tu Gmail en modo de **lectura únicamente**. Esto significa que puede:
- Leer emails sin leer
- Buscar emails
- Listar emails de contactos específicos

Pero **NO puede**:
- Enviar emails
- Eliminar emails
- Modificar emails

## Pasos de Configuración

### 1. Crear un proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto (o usa el existente)
3. Asegúrate de que el proyecto sea: `k2-proyect-491716`

### 2. Habilitar Gmail API

1. En Google Cloud Console, ve a "APIs y Servicios" → "Biblioteca"
2. Busca "Gmail API"
3. Haz clic en ella y selecciona "Habilitar"

### 3. Crear credenciales OAuth2

1. Ve a "APIs y Servicios" → "Credenciales"
2. Haz clic en "Crear credenciales" → "ID de cliente de OAuth"
3. Selecciona "Aplicación de escritorio"
4. Descarga el archivo JSON de credenciales

### 4. Configurar el archivo de credenciales

1. Descargaste un archivo `credentials.json`
2. Coloca este archivo en la carpeta raíz del proyecto (o donde ejecutes el bot)
3. Establece la variable de entorno:
   ```powershell
   $env:GMAIL_CREDENTIALS_PATH = "ruta/al/credentials.json"
   ```

### 5. Primera autenticación

Cuando ejecutes el bot por primera vez con el agente de email, se abrirá una ventana del navegador pidiendo que:
1. Inicies sesión en tu cuenta de Gmail
2. Autorices al bot a leer tus emails

Después de esto, se generará un archivo `token.json` que se reutilizará en futuras ejecuciones.

## Variables de Entorno

```bash
# Ruta al archivo de credenciales OAuth2 descargado de Google Cloud Console
GMAIL_CREDENTIALS_PATH=path/to/credentials.json

# Ruta donde se guardará el token de autenticación (se genera automáticamente)
GMAIL_TOKEN_PATH=token.json
```

## Herramientas Disponibles

Una vez configurado, el agente de email proporcionará estas herramientas:

### 1. **obtener_emails_sin_leer**
Obtiene todos los emails sin leer de tu bandeja de entrada.

**Uso ejemplo:**
```
"¿Cuáles son mis emails sin leer?"
"Muéstrame los últimos 5 emails sin leer"
```

### 2. **buscar_emails**
Busca emails por términos específicos, palabras clave, remitentes, etc.

**Uso ejemplo:**
```
"Busca emails de 'cliente'"
"Encuentra emails de usuario@gmail.com"
"Busca emails relacionados con 'proyecto'"
```

### 3. **obtener_emails_de_contacto**
Obtiene todos los emails de un remitente específico.

**Uso ejemplo:**
```
"Muéstrame los emails de maria@empresa.com"
"Dame todos los emails de soporte@gmail.com"
```

## Ejemplo de Uso

```python
# En Telegram, dirígete al bot K2 y escribe:
"K2, ¿tengo emails sin leer?"
"Busca todos los emails de mi empresa"
"Muéstrame los últimos 3 emails del equipo"
```

## Permisos y Seguridad

- ✅ Solo lectura - El bot **no puede** comprometer tu cuenta
- ✅ Token local - Las credenciales se guardan localmente
- ✅ OAuth2 - Google valida la autenticación de forma segura
- ❌ No se envían, eliminan o modifican emails

## Solución de Problemas

### Error: "No se encontraron credenciales"
- Verifica que hayas descargado el archivo `credentials.json`
- Revisa que la ruta `GMAIL_CREDENTIALS_PATH` sea correcta

### Error: "Token inválido"
- Elimina el archivo `token.json` (si existe)
- Autentica nuevamente en la próxima ejecución

### El navegador no se abre automáticamente
- Copia manualmente la URL que aparece en la terminal
- Pégala en tu navegador

## Documentación Oficial

Para más información sobre Gmail API:
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [OAuth 2.0 para aplicaciones de escritorio](https://developers.google.com/identity/protocols/oauth2/native-app)
