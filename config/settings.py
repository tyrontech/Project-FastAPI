import os
from dotenv import load_dotenv

load_dotenv()

REQUIRED_VARS = [
    "USER", "PASSWORD", "HOST", "DATABASE", "PORT"
]

for var in REQUIRED_VARS:
    if not os.getenv(var):
        raise EnvironmentError(f"⚠️ Falta la variable de entorno obligatoria: {var}")
    

# Base de datos
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
DATABASE = os.getenv("DATABASE")