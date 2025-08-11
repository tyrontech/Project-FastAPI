from fastapi import Depends, APIRouter, HTTPException 
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from argon2 import PasswordHasher

from repositories.queries_repository import read
from auth.handler import JWTAuthHandler

jwt_handler = JWTAuthHandler()
ph = PasswordHasher()

login = APIRouter()

@login.post("/login", tags=["Login"])
async def login_auth2(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await read("users", "email", form_data.username)

    if not user or not user[0].email or not user[0].password:
        raise HTTPException(status_code=400, detail="Nombre de usuario o contraseña incorrectos")

    try:
        if not ph.verify(user[0].password, form_data.password):
            raise HTTPException(status_code=400, detail="Nombre de usuario o contraseña incorrectos")
    except Exception:
        raise HTTPException(status_code=400, detail="Nombre de usuario o contraseña incorrectos")

    datos = {"email": user[0].email}
    response = JSONResponse(content={"message": "Inicio de sesión exitoso", "user": datos}, status_code=200)

    jwt_handler.set_auth_cookies(response, datos)

    return response
