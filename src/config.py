"""
Módulo de Configuración Centralizada.

Contiene las constantes globales, rutas de archivos y parámetros de conexión 
del proyecto. Centralizar estos valores facilita la portabilidad entre 
entornos (Desarrollo, Producción).

Nota de seguridad: Las credenciales sensibles (FILE_CREDS) deben estar 
listadas en el .gitignore para evitar fugas de información.
"""

# --- GOOGLE SHEETS CONFIG ---
# Ruta al archivo JSON con las llaves privadas del Service Account
FILE_CREDS = 'credentials.json'

# Nombre exacto de la hoja de cálculo en Google Drive
NOMBRE_ARCHIVO_SHEET = 'Formulario cierre (respuestas)' 

# --- DATABASE CONFIG ---
# Nombre de la base de datos para persistencia local
DB_NAME = 'negocio_analitica.db'