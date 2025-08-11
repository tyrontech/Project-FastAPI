from fastapi import Cookie, Header, Request, HTTPException

from utils.token_utils import parse_token_from_cookie, parse_token_from_header
from handler import JWTAuthHandler  


jwt_handler = JWTAuthHandler()


async def verify_csrf_token(request: Request):
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-TOKEN")
    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise HTTPException(status_code=403, detail="Validación CSRF fallida")



async def get_user_from_cookie(access_token: str = Cookie(None)) -> dict:
    token_string = parse_token_from_cookie(access_token)
    user_payload = jwt_handler.decode_token(token_string)
    return user_payload

async def get_user_from_header(authorization: str = Header(None)) -> dict:
    token_string = parse_token_from_header(authorization)
    user_payload = jwt_handler.decode_token(token_string)
    return user_payload