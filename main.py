from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.login import login

app = FastAPI()


app.include_router(login)


origins = [
    "http://127.0.0.1:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)


