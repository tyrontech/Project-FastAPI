import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Response, HTTPException, status
from jose import jwt, JWTError

# Importamos las configuraciones de un lugar centralizado
from config.settings import (
    PRIVATE_KEY, PUBLIC_KEY, ALGORITHM, TOKEN_SECONDS_EXP, ENVIRONMENT, COOKIE_DOMAIN
)

class JWTAuthHandler:
    is_production: bool
    cookie_domain: str

    def __init__(self):
        self.is_production = False
        self.cookie_domain = COOKIE_DOMAIN

    def create_access_token(self, data: dict) -> str:
        """Crea un token de acceso JWT."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(seconds=TOKEN_SECONDS_EXP)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, PRIVATE_KEY, algorithm=ALGORITHM)

    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado"
            )

    def set_auth_cookies(self, response: Response, user_data: dict):
        auth_token = self.create_access_token(user_data)
        
        response.set_cookie(
            key="access_token",
            value=f"Bearer {auth_token}",
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=TOKEN_SECONDS_EXP,
            domain=self.cookie_domain,
            path="/"
        )
        
        
        csrf_token = secrets.token_hex(16)
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,
            secure=False,
            samesite="lax",
            max_age=TOKEN_SECONDS_EXP,
            domain=self.cookie_domain,
            path="/"
        )