# """
# Pipeline principal del proyecto.

# Orquesta el flujo completo:
# EXTRACT → TRANSFORM → LOAD

# Este archivo representa el punto de entrada productivo.
# """

import pandas as pd
from datetime import datetime

from src.extraction import obtener_dolar_hibrido, obtener_ventas_sheets
from src.transformation import (
    limpiar_celda_dinero_auditado,
    calcular_impuestos,
    generar_dim_calendario,
    generar_dim_medios
)
from src.loading import cargar_datos_postgreSQL


def main():

    # =====================================================
    # 1. EXTRACT
    # =====================================================
    df_ventas = obtener_ventas_sheets()
    df_dolar = obtener_dolar_hibrido()

    if df_ventas is None or df_dolar.empty:
        print(" No se pudieron obtener los datos. Proceso cancelado.")
        return

    # =====================================================
    # 2. TRANSFORM
    # =====================================================
    print("  [TRANSFORM] Limpieza y modelado de datos")

    # Normalización de nombres de columnas
    df_ventas.columns = df_ventas.columns.str.strip()

    # ----------------------
    # Conversión de fechas 
    # ----------------------
    df_ventas["fecha_dt"] = pd.to_datetime(
        df_ventas["Fecha"],
        dayfirst=True,
        errors="coerce"
    )

    # Eliminamos fechas inválidas (NaT)
    df_ventas = df_ventas.dropna(subset=["fecha_dt"])

    # -----------------------------------------------------
    # Auditoría explícita de fechas
    # -----------------------------------------------------
    FECHA_MIN = pd.Timestamp("2020-01-01")
    FECHA_MAX = pd.Timestamp.today()

    df_ventas["fecha_fuera_de_rango"] = (
        (df_ventas["fecha_dt"] < FECHA_MIN) |
        (df_ventas["fecha_dt"] > FECHA_MAX)
    ).astype(int)

    df_ventas["nota_fecha"] = df_ventas["fecha_fuera_de_rango"].apply(
        lambda x: "FECHA_FUERA_DE_RANGO" if x == 1 else "OK"
    )

    # -----------------------------------------------------
    # Exclusión explícita del análisis principal
    # -----------------------------------------------------
    df_ventas_validas = df_ventas[df_ventas["fecha_fuera_de_rango"] == 0].copy()
    df_ventas = df_ventas_validas

    # -----------------------------------------------------
    # Deduplicación
    # -----------------------------------------------------
    cols_control = ["fecha_dt", "Turno", "C", "T", "MP (NEGOCIO)","MP Usuario E","MP Usuario F","MP Usuario A", "M","Revendedores solo números"]
    cols_check = [c for c in cols_control if c in df_ventas.columns]

    rows_before = len(df_ventas)

    df_ventas = df_ventas.drop_duplicates(
        subset=cols_check,
        keep="first"
    )

    rows_after = len(df_ventas)
    rows_removed = rows_before - rows_after

    print(f" DEDUPLICACIÓN: se eliminaron {rows_removed} registros duplicados")

    # -----------------------------------------------------
    # Merge con cotización del dólar
    # -----------------------------------------------------
    df_ventas = df_ventas.sort_values("fecha_dt")

    df_merged = pd.merge(
        df_ventas,
        df_dolar,
        left_on="fecha_dt",
        right_on="fecha",
        how="left"
    )

    # -----------------------------------------------------
    # Normalización de columnas monetarias (MELT)
    # -----------------------------------------------------
    cols_dinero = [
        "C",
        "T",
        "M",
        "Revendedores solo números",
        "MP (NEGOCIO)",
        "MP Usuario E",
        "MP Usuario F",
        "MP Usuario A"
    ]

    cols_reales = [c for c in cols_dinero if c in df_merged.columns]

    df_melt = df_merged.melt(
        id_vars=["fecha_dt", "cotizacion_blue", "Turno"],
        value_vars=cols_reales,
        var_name="medio_pago_origen",
        value_name="valor_sucio"
    )

    # -----------------------------------------------------
    # Limpieza monetaria + auditoría de texto
    # -----------------------------------------------------
    df_melt[["monto_ars", "notas_auditoria"]] = df_melt.apply(
        lambda row: limpiar_celda_dinero_auditado(row, "valor_sucio"),
        axis=1
    )

    df_fact = df_melt[df_melt["monto_ars"] > 0].copy()

    # -----------------------------------------------------
    # KPIs monetarios
    # -----------------------------------------------------
    df_fact["monto_usd"] = df_fact.apply(
        lambda x: x["monto_ars"] / x["cotizacion_blue"]
        if x["cotizacion_blue"] > 0 else 0,
        axis=1
    )

    medios_fiscales = ["C", "T", "MP (NEGOCIO)"]

    df_fact["es_fiscal"] = df_fact["medio_pago_origen"].apply(
        lambda x: 1 if x in medios_fiscales else 0
    )

    df_fact[["monto_neto", "impuesto_iva", "impuesto_iibb", "tasa_syh"]] = (
        df_fact.apply(calcular_impuestos, axis=1)
    )

    # Neto en USD (MISMA cotización)
    df_fact["monto_neto_usd"] = df_fact.apply(
        lambda x: x["monto_neto"] / x["cotizacion_blue"]
        if x["cotizacion_blue"] > 0 else 0,
        axis=1
    )

    # -----------------------------------------------------
    # Redondeo
    # -----------------------------------------------------
    cols_numericas = [
        "monto_ars",
        "monto_usd",
        "monto_neto",
        "monto_neto_usd",
        "impuesto_iva",
        "impuesto_iibb",
        "tasa_syh"
    ]

    df_fact[cols_numericas] = df_fact[cols_numericas].round(4)

    # -----------------------------------------------------
    # Clave de fecha (date, no string)
    # -----------------------------------------------------
    df_fact["fecha_id"] = df_fact["fecha_dt"].dt.date

    # -----------------------------------------------------
    # Dimensiones
    # -----------------------------------------------------
    df_dim_cal = generar_dim_calendario(df_ventas)
    df_dim_medios = generar_dim_medios()

    df_dim_cot = df_dolar.copy()
    df_dim_cot["fecha_id"] = df_dim_cot["fecha"].dt.date
    df_dim_cot = df_dim_cot[["fecha_id", "cotizacion_blue"]]

    # =====================================================
    # 3. LOAD
    # =====================================================
    cargar_datos_postgreSQL(
        df_fact,
        df_dim_cal,
        df_dim_medios,
        df_dim_cot
    )

    print("-" * 40)
    print(" PIPELINE FINALIZADO CORRECTAMENTE")
    print("-" * 40)


if __name__ == "__main__":
    main()



