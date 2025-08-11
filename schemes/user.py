# schemes/user_scheme.py

from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr  # <-- Este es el cambio clave
    password: str
