from fastapi import HTTPException, status
from typing import Optional


def parse_token_from_cookie(access_token: str) -> str:
    if access_token is None:
        raise HTTPException(status_code=400, detail="Cookie 'access_token' not found")
    
    # Asumimos que el formato es "Bearer <token>"
    parts = access_token.split(" ")
    if len(parts) == 2 and parts[0] == "Bearer":
        return parts[1]
    
    # Si no tiene el formato "Bearer", devolvemos el valor crudo
    return access_token





def parse_token_from_header(authorization: Optional[str]) -> str:
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cabecera 'Authorization' no encontrada"
        )
    
    # Divide el string para separar "Bearer" del token real.
    parts = authorization.split(" ")
    
    # Verifica que el formato sea exactamente "Bearer <token>".
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de token inválido. Se requiere 'Bearer <token>'."
        )
    
    return parts[1]