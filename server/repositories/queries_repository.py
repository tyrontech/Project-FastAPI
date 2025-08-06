from sqlalchemy import select, insert, or_, and_, desc, asc, func
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from typing import Dict, Any, Union, List

from config.db import async_session, get_table



async def create(table_name: str, schema_or_dict:Union[BaseModel, dict]) -> Dict[str, Any]:
    """
    Inserta un registro usando metadata y esquema Pydantic
    """
    # Obtener la tabla
    table = await get_table(table_name)
    
    if isinstance(schema_or_dict, BaseModel):
        values = schema_or_dict.model_dump(exclude_none=True)
    elif isinstance(schema_or_dict, dict):
        values = {k: v for k, v in schema_or_dict.items() if v is not None}
    else:
        raise ValueError("Los datos deben ser un BaseModel o un dict")
    
    # Crear la query de inserción
    stmt = table.insert().values(**values).returning(table)
    
    async with async_session() as session:
        result = await session.execute(stmt)
        new_record = result.fetchone()
        await session.commit()
        
        return dict(new_record._mapping)




async def bulk_create(table_name: str, schemas: List[BaseModel]):
    try:
        table = await get_table(table_name)
        
        values_list = [schema.model_dump() for schema in schemas]
        
        async with async_session() as session:
            try:
                await session.execute(
                    insert(table),
                    values_list
                )
                
                await session.commit()
                
                return {
                    "status": 200,
                    "data": values_list,
                    "message": f"Se crearon {len(values_list)} registros exitosamente"
                }
            
            except IntegrityError as e:
                await session.rollback()
                
                error_message = str(e.orig)
                
                if "Duplicate entry" in error_message:
                    column_name = error_message.split("key '")[1].split("'")[0].split('.')[-1]
                    duplicate_value = error_message.split("Duplicate entry '")[1].split("'")[0]
                    
                    return {
                        "status": 400,
                        "message": f"Ya existe un registro con valor '{duplicate_value}' para la columna '{column_name}'",
                        "error_code": "DUPLICATE_ENTRY"
                    }
                
                return {
                    "status": 400,
                    "message": f"Error de integridad en la base de datos: {str(e)}",
                    "error_code": "INTEGRITY_ERROR"
                }
                
    except Exception as e:
        return {
            "status": 500,
            "message": f"Error al crear registros en masa: {str(e)}"
        }
     




async def create_multiple_atomic(table_schemas: Dict[str, List[Union[BaseModel, dict]]]):
    results = {}
    total_records = 0
    
    async with async_session() as session:
        try:
            async with session.begin():
                # Recorrer cada tabla y sus esquemas
                for table_name, schemas_or_dicts in table_schemas.items():
                    table = await get_table(table_name)
                    
                    if not schemas_or_dicts:  # Si la lista está vacía, continuar con la siguiente tabla
                        continue
                    
                    # Obtener el nombre de la columna primary key
                    primary_key_column = None
                    for column in table.columns:
                        if column.primary_key:
                            primary_key_column = column.name
                            break
                    
                    # Convertir cada elemento a diccionario según su tipo
                    values_list = []
                    for schema_or_dict in schemas_or_dicts:
                        if isinstance(schema_or_dict, BaseModel):
                            values = schema_or_dict.model_dump(exclude_none=True)
                        elif isinstance(schema_or_dict, dict):
                            values = {k: v for k, v in schema_or_dict.items() if v is not None}
                        else:
                            raise ValueError(f"Los datos para la tabla {table_name} deben ser BaseModel o dict")
                        values_list.append(values)
                    
                    if values_list:  # Solo insertar si hay valores
                        records_with_ids = []
                        
                        if len(values_list) == 1:
                            # Para inserción única, usar insert().values() que retorna el ID
                            ins = table.insert().values(values_list[0])
                            result = await session.execute(ins)
                            
                            # Obtener el ID insertado
                            inserted_id = result.inserted_primary_key[0] if result.inserted_primary_key else None
                            
                            record = values_list[0].copy()
                            if inserted_id and primary_key_column:
                                record[primary_key_column] = inserted_id
                            records_with_ids.append(record)
                            
                        else:
                            # Para múltiples inserciones, usar returning para obtener los IDs
                            if primary_key_column:
                                ins = table.insert().values(values_list).returning(getattr(table.c, primary_key_column))
                                result = await session.execute(ins)
                                inserted_ids = [row[0] for row in result.fetchall()]
                                
                                # Combinar los valores insertados con sus IDs
                                for i, values in enumerate(values_list):
                                    record = values.copy()
                                    if i < len(inserted_ids):
                                        record[primary_key_column] = inserted_ids[i]
                                    records_with_ids.append(record)
                            else:
                                # Si no hay primary key, solo insertar sin retornar IDs
                                ins = table.insert().values(values_list)
                                await session.execute(ins)
                                records_with_ids = values_list.copy()
                        
                        # Guardar resultados para esta tabla
                        results[table_name] = records_with_ids
                        total_records += len(records_with_ids)
                
                # El commit se hace automáticamente al salir del session.begin()
                return {
                    "status": 200,
                    "data": results,
                    "message": f"Se crearon {total_records} registros exitosamente en {len(results)} tablas"
                }
                
        except IntegrityError as e:
            # El rollback se maneja automáticamente gracias al context manager
            raise e
        except Exception as e:
            # Cualquier otro error también provoca rollback automático
            raise e



async def read(table_name: str, filter_column=None, filter_value=None):
    table = await get_table(table_name)
    
    query = select(table)

    if filter_value is not None:
        query = query.where(getattr(table.c, filter_column) == filter_value)

    try:
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(query)
                return result.mappings().all()
    except Exception as e:
        # Manejar cualquier error que pueda ocurrir
        print(f"Error al leer de la base de datos: {e}")
        raise





async def read_paginated(
    table_name: str,
    filters: dict,
    page: int = 1,
    limit: int = 20,
    operator: str = 'and',
    order_by_column: str = 'id',  # Parámetro para ordenar, con un default común como 'id'
    order_direction: str = 'asc'  # Parámetro opcional para la dirección
):
    op_lower = operator.lower()
    if op_lower not in ['and', 'or']:
        raise ValueError("Operador no válido. Use 'and' o 'or'.")

    table = await get_table(table_name)

    conditions = []
    if filters:
        for column, value in filters.items():
            if value is not None and value != '':
                if isinstance(value, str):
                    condition = getattr(table.c, column).ilike(f"%{value}%")
                else:
                    condition = getattr(table.c, column) == value
                conditions.append(condition)

    where_clause = None
    if conditions:
        if op_lower == 'or':
            where_clause = or_(*conditions)
        else:
            where_clause = and_(*conditions)

    try:
        async with async_session() as session:
            # ... (la consulta de conteo sigue igual) ...
            count_query = select(func.count()).select_from(table)
            if where_clause is not None:
                count_query = count_query.where(where_clause)
            
            total_result = await session.execute(count_query)
            total_records = total_result.scalar_one()

            order_column = getattr(table.c, order_by_column)

            # 2. Determinamos la dirección del ordenamiento
            if order_direction.lower() == 'desc':
                order_expression = desc(order_column)
            else:
                order_expression = asc(order_column)

            data_query = select(table).limit(limit).offset((page - 1) * limit).order_by(order_expression)
            
            if where_clause is not None:
                data_query = data_query.where(where_clause)

            data_result = await session.execute(data_query)
            datos = data_result.mappings().all()

            return {
                "metadata": {
                    "total_registros": total_records,
                    "pagina_actual": page,
                    "limite_por_pagina": limit,
                    "total_paginas": (total_records + limit - 1) // limit if limit > 0 else 0,
                },
                "datos": datos
            }
            
    except AttributeError:
        # Capturamos el error si la columna de ordenamiento no existe
        raise ValueError(f"La columna de ordenamiento '{order_by_column}' no existe en la tabla '{table_name}'.")
    except Exception as e:
        print(f"Error al buscar de forma paginada: {e}")
        raise



async def update(table_name: str, schema_or_dict:Union[BaseModel, dict], filter_column: str): 
    try:
        table = await get_table(table_name)        

        if isinstance(schema_or_dict, BaseModel):
            values = schema_or_dict.model_dump(exclude_none=True)
        elif isinstance(schema_or_dict, dict):
            values = {k: v for k, v in schema_or_dict.items() if v is not None}
        else:
            raise ValueError("Los datos deben ser un BaseModel o un dict")

        if filter_column not in values:
            return {
                "status": 400,
                "message": f"El campo '{filter_column}' no está presente en los datos del esquema."
            }

        query = table.update().where(getattr(table.c, filter_column) == values[filter_column])
        query = query.values(values)


        async with async_session() as session:
            async with session.begin():
                result = await session.execute(query)
                await session.commit()

        if result.rowcount == 0:
            return {
                "status": 404,
                "message": "No se encontró el registro para actualizar."
            }

        return {
            "status": 200,
            "message": "Actualización exitosa"
        }
    
    except Exception as e:
        return {
            "status": 500,
            "message": f"Error al actualizar: {str(e)}"
        }
    




async def update_multiple_atomic(
    table_schemas: Dict[str, Dict[str, Union[str, List[Union[BaseModel, dict]]]]]
):
    results = {}
    total_updates = 0

    async with async_session() as session:
        try:
            async with session.begin():
                for table_name, config in table_schemas.items():
                    table = await get_table(table_name)

                    filter_column = config.get("filter_column")
                    data_items = config.get("data", [])

                    if not filter_column or not isinstance(data_items, list):
                        raise ValueError(f"La configuración para la tabla '{table_name}' es inválida.")

                    updated_rows = []

                    for item in data_items:
                        if isinstance(item, BaseModel):
                            values = item.model_dump(exclude_none=True)
                        elif isinstance(item, dict):
                            values = {k: v for k, v in item.items() if v is not None}
                        else:
                            raise ValueError(f"Los datos para la tabla '{table_name}' deben ser BaseModel o dict.")

                        if filter_column not in values:
                            raise ValueError(f"El campo '{filter_column}' no está presente en los datos para la tabla '{table_name}'.")

                        query = table.update().where(
                            getattr(table.c, filter_column) == values[filter_column]
                        ).values(values)

                        result = await session.execute(query)

                        if result.rowcount == 0:
                            raise ValueError(
                                f"No se encontró un registro con {filter_column}={values[filter_column]} en la tabla '{table_name}'."
                            )

                        updated_rows.append(values)
                        total_updates += 1

                    if updated_rows:
                        results[table_name] = updated_rows

                return {
                    "status": 200,
                    "data": results,
                    "message": f"Se actualizaron {total_updates} registros exitosamente en {len(results)} tablas."
                }

        except (IntegrityError, ValueError) as e:
            return {
                "status": 400,
                "message": f"Actualización fallida: {str(e)}"
            }
        except Exception as e:
            return {
                "status": 500,
                "message": f"Error inesperado al actualizar múltiples registros: {str(e)}"
            }
        




async def delete(table_name: str, filter_column: str, filter_value):
    table = await get_table(table_name)
    
    async with async_session() as session:
        try:
            async with session.begin():
                # Primero verificamos si el registro existe
                check_query = select(table).where(getattr(table.c, filter_column) == filter_value)
                result = await session.execute(check_query)
                record = result.first()
                
                if not record:
                    return {
                        "status": "error",
                        "message": f"No se encontró el registro con {filter_column}={filter_value}",
                        "error_code": "RECORD_NOT_FOUND"
                    }
                
                # Crear la consulta de eliminación
                delete_query = table.delete().where(getattr(table.c, filter_column) == filter_value)
                
                # Ejecutar la consulta
                result = await session.execute(delete_query)
                await session.commit()
                
                # Obtener el número de filas afectadas
                rows_deleted = result.rowcount
                
                return {
                    "status": 200,
                    "message": f"Registro eliminado exitosamente. Filas afectadas: {rows_deleted}",
                    "rows_affected": rows_deleted
                }
        except Exception as e:
            # Si ocurre cualquier error, hacemos rollback
            await session.rollback()
            
            # Determinar el tipo de error
            if isinstance(e, IntegrityError):
                error_message = str(e.orig)
                
                # Manejar error de restricción de clave foránea
                if "foreign key constraint fails" in error_message.lower():
                    return {
                        "status": "error",
                        "message": f"No se puede eliminar el registro porque está siendo referenciado por otros registros",
                        "error_code": "FOREIGN_KEY_CONSTRAINT"
                    }
                
            # Devolver error genérico
            return {
                "status": "error",
                "message": f"Error al eliminar el registro: {str(e)}",
                "error_code": "DELETE_ERROR"
            }





async def use_function(function_name: str, *args: Any):
    try:
        # Obtener la función dinámica desde func
        funcion_sql = getattr(func, function_name)

        if not funcion_sql:
            raise AttributeError(f"La función '{function_name}' no existe en SQLAlchemy.func")
        
        # Armar el SELECT con los argumentos
        stmt = select(funcion_sql(*args))

        async with async_session() as session:
            result = await session.execute(stmt)
            return {
                "status": 200,
                "data": result.scalars().all()
            }

    except AttributeError:
        return {
            "status": 400,
            "message": f"La función '{function_name}' no es válida en SQLAlchemy.func"
        }

    except Exception as e:
        return {
            "status": 500,
            "message": f"Error al ejecutar la función '{function_name}': {str(e)}"
        }
    

    

