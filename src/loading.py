"""
Módulo de carga de datos (LOAD).

Responsabilidades:
- Persistir tablas de hechos y dimensiones en PostgreSQL.
- Utilizar SQLAlchemy como capa de abstracción.
- Preparar el modelo para consumo analítico (Power BI).

Notas:
- Se utiliza `if_exists='replace'` por tratarse de un pipeline batch.
- El modelo está pensado como esquema analítico (star schema).
"""

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.types import Date


def cargar_datos_postgreSQL(df_fact, df_dim_cal, df_dim_medios, df_dim_cot):
    """
    Carga las tablas del modelo analítico en PostgreSQL.

    Tablas:
    - fact_ingresos
    - dim_calendario
    - dim_medios_pago
    - dim_cotizacion
    """

    print(" [LOAD] Conectando a PostgreSQL (Docker) en puerto 5440...")

    # Cadena de conexión local (Docker)
    cadena_conexion = (
        'postgresql+psycopg2://postgres:'
        'nueva_pass_123@127.0.0.1:5440/negocio_analitica'
    )

    engine = create_engine(
        cadena_conexion,
        connect_args={'client_encoding': 'utf8'}
    )

    try:
        # --- TABLA DE HECHOS ---
        cols_fact = [
            'fecha_id', 'medio_pago_origen', 'Turno',
            'monto_ars', 'monto_usd', 'es_fiscal',
            'monto_neto', 'monto_neto_usd',
            'impuesto_iva', 'impuesto_iibb', 'tasa_syh',
            'notas_auditoria'
        ]

        df_fact[cols_fact].to_sql(
            'fact_ingresos',
            engine,
            if_exists='replace',
            index=False,
            dtype={'fecha_id': Date()}
        )

        # --- DIMENSIONES ---
        df_dim_cal.to_sql(
            'dim_calendario',
            engine,
            if_exists='replace',
            index=False,
            dtype={'fecha_id': Date()}
        )

        df_dim_medios.to_sql(
            'dim_medios_pago',
            engine,
            if_exists='replace',
            index=False
        )

        df_dim_cot.to_sql(
            'dim_cotizacion',
            engine,
            if_exists='replace',
            index=False,
            dtype={'fecha_id': Date()}
        )

        print(" [LOAD] ¡Datos cargados correctamente!")

    except Exception as e:
        print(f" [LOAD] Error al cargar datos: {repr(e)}")
        print("   -> Verificar que Docker esté activo y el puerto expuesto.")



