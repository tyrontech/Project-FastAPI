from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
from config import settings


db_user = settings.USER
db_password = settings.PASSWORD
db_host = settings.HOST
db_port = settings.PORT
db_name = settings.DATABASE


DATABASE_URL_ASYNC = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

async_engine = create_async_engine(DATABASE_URL_ASYNC, echo=True, pool_pre_ping=True, future=True)

async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

metadata = MetaData()

_flags = {"is_loaded": False}

def cargar_metadata(sync_conn):
    metadata.reflect(bind=sync_conn, views=True)



async def load_all_metadata():
    if not _flags["is_loaded"]:
        async with async_engine.connect() as conn:
            await conn.run_sync(cargar_metadata)
        _flags["is_loaded"] = True
        print(f"Metadatos cargados con {len(metadata.tables)} tablas")




async def get_table_sync(table_name: str):
    if not _flags["is_loaded"]:
        raise RuntimeError("Metadatos no cargados. Ejecuta 'await load_all_metadata()' primero")
    
    if table_name not in metadata.tables:
        raise ValueError(f"Tabla '{table_name}' no encontrada")
    
    return metadata.tables[table_name]




async def get_table(table_name: str):
    if not _flags["is_loaded"]:
        await load_all_metadata()
    
    return await get_table_sync(table_name)