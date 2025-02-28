# Registrador de Tiempo para Tempo

Esta herramienta te permite registrar tus horas trabajadas en Tempo de manera rápida y sencilla desde tu computadora.

## 💻 Prerrequisitos

### Instalar Python (solo una vez)

#### Para usuarios de Mac:
1. Abre Terminal
2. Instala Homebrew (gestor de paquetes) pegando este comando y presionando Enter:
   ```
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. Una vez instalado Homebrew, instala Python:
   ```
   brew install python
   ```

#### Para usuarios de Windows:
1. Descarga Python desde la página oficial: https://www.python.org/downloads/
2. Haz clic en "Download Python" (descarga la última versión)
3. **IMPORTANTE**: Durante la instalación, marca la casilla que dice "Add Python to PATH"
4. Sigue las instrucciones del instalador haciendo clic en "Next"

### Instalar Dependencias (solo una vez)
1. Descarga el archivo `requirements.txt` y colócalo en la misma carpeta que `time_logger.py`
2. Abre Terminal (Mac) o Command Prompt (Windows)
3. Navega hasta la carpeta donde están los archivos:
   ```
   cd ruta/a/la/carpeta
   ```
4. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

## 🔑 Configuración Inicial (solo una vez)

### 1. Configurar el archivo config.json
1. Copia el archivo `config.example.json` y renómbralo como `config.json`
2. Abre `config.json` con tu editor de texto favorito
3. Actualiza los siguientes valores con tu información:
   ```json
   {
       "jira": {
           "url": "https://TUEMPRESA.atlassian.net",  // URL de tu Jira
           "email": "tu.email@tuempresa.com",         // Tu correo de Jira
           "api_token": "TU_TOKEN_DE_JIRA",          // Token de API de Jira
           "account_id": "TU_ACCOUNT_ID"             // Tu Account ID de Jira
       },
       "tempo": {
           "api_token": "TU_TOKEN_DE_TEMPO"          // Token de API de Tempo
       }
   }
   ```

### 2. Obtener tu Token de Tempo API
1. Ve a la configuración de Tempo en Jira: [Tempo > Settings > API Integration]
2. En tu navegador, abre: https://TUEMPRESA.atlassian.net/plugins/servlet/ac/io.tempo.jira/tempo-app#!/configuration/api-integration
3. Copia el token generado
4. Pégalo en el campo `api_token` de la sección `tempo` en tu `config.json`

### 3. Obtener tu Token de Jira
1. Ve a la página de tokens de API de Atlassian: https://id.atlassian.com/manage-profile/security/api-tokens
2. Haz clic en "Create API token"
3. Dale un nombre (por ejemplo: "Registrador de Tiempo")
4. Copia el token generado
5. Pégalo en el campo `api_token` de la sección `jira` en tu `config.json`

### 4. Obtener tu Account ID de Jira
1. Ve a tu perfil de Jira
2. En la URL de tu perfil, copia el ID que aparece después de "people/"
   - Ejemplo: Si la URL es `https://TUEMPRESA.atlassian.net/jira/people/557058:822cb66b-e880-4f1d-9e33-ba19ed84c40a`
   - Tu Account ID es: `557058:822cb66b-e880-4f1d-9e33-ba19ed84c40a`
3. Pégalo en el campo `account_id` de la sección `jira` en tu `config.json`

## 🚀 Cómo Usar

### Para usuarios de Mac:
1. Abre la aplicación "Terminal" (puedes encontrarla usando Spotlight - presiona `⌘ + Espacio` y escribe "Terminal")
2. Navega hasta la carpeta donde está el script usando el comando:
   ```
   cd ruta/a/la/carpeta
   ```
3. Ejecuta el programa con:
   ```
   python time_logger.py
   ```

### Para usuarios de Windows:
1. Abre "Símbolo del sistema" (Command Prompt) - puedes encontrarlo buscando "cmd" en el menú inicio
2. Navega hasta la carpeta donde está el script usando el comando:
   ```
   cd ruta\a\la\carpeta
   ```
3. Ejecuta el programa con:
   ```
   python time_logger.py
   ```

## 📝 ¿Qué información necesitarás?

Cuando ejecutes el programa, te pedirá:

1. **ID del Ticket de Jira** (ejemplo: INT0012-92)
2. **Horas trabajadas** (ejemplo: 2.5)
3. **Descripción** del trabajo realizado
4. **¿Es facturable?** (responde 'y' para sí o 'n' para no)
5. **Fecha** (presiona Enter para usar la fecha de hoy, o ingresa una fecha en formato YYYY-MM-DD)

## ⚠️ Importante
- No puedes registrar tiempo para fechas anteriores a 30 días
- Si hay algún problema de conexión, tus registros se guardarán localmente
- Asegúrate de tener una conexión a internet activa
- Guarda una copia de tus tokens en un lugar seguro
- **NUNCA** compartas tu archivo `config.json` ni lo subas a repositorios públicos

## 🆘 ¿Problemas?

¿Necesitas ayuda? ¡Estamos aquí para apoyarte! 

### 📬 Contacto

```
  ┌──────────────────────────────────┐
  │                                  │
  │   Jorge Bastidas                 │
  │   ✉️  indiegente@proton.me       │
  │   🔒 Comunicación Encriptada     │
  │                                  │
  └──────────────────────────────────┘
```

> 💡 **Tip**: Para una respuesta más rápida, incluye en tu correo:
> - El error que estás viendo
> - El ID del ticket de Jira
> - La fecha y hora del intento 