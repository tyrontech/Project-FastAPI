from pydantic import BaseModel
from datetime import date
from typing import Literal, Optional


class Vendedor(BaseModel):
    nom_ven: str
    ape_ven: str
    sue_ven: float
    fin_ven: date  
    tip_ven: str



class Producto(BaseModel):
    des_pro: str 
    pre_pro: float
    sac_pro: int  
    smi_pro: int  
    uni_pro: str 
    lin_pro: str 
    imp_pro: Literal['F', 'V'] 



class DetalleFactura(BaseModel):
    num_fac: Optional[str] = None
    cod_pro: str
    can_ven: int                      
    pre_ven: float     


class Factura(BaseModel):                              
    est_fac: str = "Pendiente"
    cod_ven: str
    por_igv: float 
    detalle_factura: list[DetalleFactura]       


              