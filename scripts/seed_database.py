import asyncio
import random
import string

from argon2 import PasswordHasher

from repositories.queries_repository import create
from schemes.user import UserCreate


# --- 1. Preparación ---
ph = PasswordHasher()

def generate_random_string(length=12):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

# --- 2. Función Principal ---
async def create_and_save_test_user():
    print("🚀 Iniciando la creación de un usuario de prueba...")

    # Generamos un correo y contraseña aleatorios
    test_email = f"user_{generate_random_string(6).lower()}@test.com"
    test_password = generate_random_string(16) # Contraseña segura de 16 caracteres
    
    print(f"   - Email generado: {test_email}")
    print(f"   - Contraseña generada: {test_password}")

    # Hasheamos la contraseña
    hashed_password = ph.hash(test_password)
    print("   - Contraseña hasheada con Argon2.")

    # Creamos el objeto de usuario usando el esquema Pydantic
    user_data = UserCreate(
        email=test_email,
        password=hashed_password
    )

    # --- 3. Guardado en la Base de Datos ---
    try:
        new_user = await create("users", user_data)
        print("-" * 30)
        print(f"✅ ¡Éxito! Usuario creado con ID: {new_user['id']} y Email: {new_user['email']}")
        print("-" * 30)
    except Exception as e:
        print(f"❌ Error al guardar en la base de datos: {e}")

# --- 4. Ejecución del Script ---
if __name__ == "__main__":
    # Ejecutamos la función asíncrona
    asyncio.run(create_and_save_test_user())