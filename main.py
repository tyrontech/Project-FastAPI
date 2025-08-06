from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from repositories.queries_repository import create, read
from schemes.schemes import Vendedor, Producto, Factura, DetalleFactura

app = FastAPI()


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


@app.post("/vendedor", tags=["Vendedor"])
async def root(vendedor: Vendedor):
    result = await create("vendedor", vendedor)
    return result



@app.get("/vendedor", tags=["Vendedor"])
async def root():
    result = await read("vendedor")
    return result



@app.delete("/vendedor", tags=["Vendedor"])
async def root():
    pass




@app.post("/producto", tags=["Producto"])
async def root(producto: Producto):
    result = await create("producto", producto)
    return result



@app.get("/producto", tags=["Producto"])
async def root():
    result = await read("producto")
    return result




@app.post("/factura", tags=["Factura"])
async def crear_factura(factura: Factura):
    detalles = factura.detalle_factura
    datos_factura = factura.model_dump(exclude={"detalle_factura"})

    # Insertar la factura
    result_factura = await create("factura", datos_factura)
    num_fac = result_factura["num_fac"]

    detalles_creados = []
    for item in detalles:
        item_data = item.model_dump()
        item_data["num_fac"] = num_fac
        detalle_result = await create("detalle_factura", item_data)
        detalles_creados.append(detalle_result)

    
    factura_response = factura.model_copy(deep=True)
    factura_response.detalle_factura = [DetalleFactura(**d) for d in detalles_creados]
    factura_response = factura_response.model_copy(update={"num_fac": num_fac})

    return factura_response



@app.get("/factura", tags=["Factura"])
async def read_facturas():
    result = await read("vista_factura_vendedor_productos")
    return result



