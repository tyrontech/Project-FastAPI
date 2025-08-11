import os
from dotenv import load_dotenv

load_dotenv()

REQUIRED_VARS = [
    "USER", "PASSWORD", "HOST", "DATABASE", "PORT",
    "PRIVATE_KEY_PATH", "PUBLIC_KEY_PATH", "ALGORITHM", "TOKEN_SECONDS_EXP"
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


PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH")
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH")

with open(PRIVATE_KEY_PATH, "rb") as f:
    PRIVATE_KEY = f.read()

with open(PUBLIC_KEY_PATH, "rb") as f:
    PUBLIC_KEY = f.read()

ALGORITHM = os.getenv("ALGORITHM")
TOKEN_SECONDS_EXP = int(os.getenv("TOKEN_SECONDS_EXP"))

ENVIRONMENT = os.getenv("ENVIRONMENT")
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN")
