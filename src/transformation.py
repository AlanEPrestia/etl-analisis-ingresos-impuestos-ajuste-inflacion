"""
Módulo de transformación (TRANSFORM).

Responsabilidades:
- Limpieza avanzada de campos monetarios.
- Auditoría de datos inconsistentes.
- Cálculo de impuestos.
- Generación de tablas dimensionales.

Este módulo concentra la lógica de negocio.
"""

import pandas as pd
import re


def limpiar_celda_dinero_auditado(fila, col_nombre):
    """
    Limpia y normaliza valores monetarios provenientes de texto libre.

    Casos contemplados:
    - Valores en pesos
    - Valores en dólares (requiere cotización)
    - Texto mezclado
    - Errores comunes de carga
    - Fechas mal ingresadas

    Retorna:
        Series:
        - monto_ars (float)
        - notas_auditoria (str)
    """

    valor = fila.get(col_nombre, 0)
    cotizacion = fila['cotizacion_blue']

    if pd.isna(cotizacion):
        cotizacion = 0.0

    texto = str(valor).lower().strip()

    if not texto or texto in ['nan', 'none']:
        return pd.Series([0.0, 'VACIO'])

    total_ars = 0.0
    notas = []

    # --- DÓLARES ---
    patron_usd = r'(\d+[.,]?\d*)\s*(?:u\$|usd|us|dolar)'
    coincidencias_usd = re.findall(patron_usd, texto)

    if coincidencias_usd:
        notas.append("CONVERSION_USD")

    for monto_str in coincidencias_usd:
        try:
            monto_clean = monto_str.replace(',', '.')
            if cotizacion > 0:
                total_ars += float(monto_clean) * cotizacion
            texto = texto.replace(monto_str, "", 1)
        except Exception:
            pass

    # --- PESOS ---
    texto_con_letras = bool(re.search(r'[a-zA-Z]', texto))
    texto_limpio = re.sub(r'(?:u\$|usd|us|dolar|\$)', '', texto)

    posibles_numeros = re.findall(r'[\d.,]+', texto_limpio)

    for num_str in posibles_numeros:
        try:
            n_clean = num_str.replace('.', '').replace(',', '.')
            if n_clean in ['', '.', ',']:
                continue

            val = float(n_clean)

            # Heurística: detección de años cargados como montos
            if 2020 < val < 2030 and len(posibles_numeros) == 1:
                notas.append("POSIBLE_FECHA_IGNORADA")
            else:
                total_ars += val

        except Exception:
            continue

    if texto_con_letras and "CONVERSION_USD" not in notas:
        notas.append("LIMPIEZA_TEXTO")

    if not notas:
        notas.append("NORMAL")

    return pd.Series([total_ars, " + ".join(notas)])


def calcular_impuestos(row):
    """
    Calcula impuestos estimados según condición fiscal.

    Supuestos:
    - IVA 21%
    - IIBB 2.9%
    - Tasa SYH 0.3%
    """

    monto_bruto = row['monto_ars']

    if row['es_fiscal'] == 1:
        neto = monto_bruto / 1.21
        iva = monto_bruto - neto
        iibb = neto * 0.029
        syh = neto * 0.003
    else:
        neto = monto_bruto
        iva = iibb = syh = 0.0

    return pd.Series([neto, iva, iibb, syh])


def generar_dim_calendario(df_ventas):
    """
    Genera dimensión calendario continua a partir del rango de ventas.
    """

    min_date = df_ventas['fecha_dt'].min()
    max_date = df_ventas['fecha_dt'].max()

    fechas = pd.date_range(start=min_date, end=max_date)

    df_cal = pd.DataFrame({'fecha_dt': fechas})

    df_cal['fecha_id'] = df_cal['fecha_dt'].dt.date
    df_cal['año'] = df_cal['fecha_dt'].dt.year
    df_cal['mes'] = df_cal['fecha_dt'].dt.month
    df_cal['dia'] = df_cal['fecha_dt'].dt.day

    meses_esp = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }

    dias_esp = {
        0: 'Lunes', 1: 'Martes', 2: 'Miércoles',
        3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
    }

    df_cal['nombre_mes'] = df_cal['mes'].map(meses_esp)
    df_cal['nombre_dia'] = df_cal['fecha_dt'].dt.dayofweek.map(dias_esp)
    df_cal['es_fin_de_semana'] = (
        df_cal['fecha_dt'].dt.dayofweek.isin([5, 6]).astype(int)
    )

    return df_cal.drop(columns=['fecha_dt'])


def generar_dim_medios():
    """
    Genera la dimensión de medios de pago con clasificación fiscal.
    """

    datos = [
        {'id_medio': 'C', 'nombre': 'Efectivo (Caja)', 'tipo': 'Físico', 'es_fiscal': 1},
        {'id_medio': 'T', 'nombre': 'Tarjeta', 'tipo': 'Digital', 'es_fiscal': 1},
        {'id_medio': 'MP (NEGOCIO)', 'nombre': 'MercadoPago Oficial', 'tipo': 'Digital', 'es_fiscal': 1},
        {'id_medio': 'M', 'nombre': 'Monedero (Informal)', 'tipo': 'Físico', 'es_fiscal': 0},
        {'id_medio': 'Revendedores solo números', 'nombre': 'Cobro Revendedores', 'tipo': 'Físico', 'es_fiscal': 0},
        {'id_medio': 'MP Usuario E', 'nombre': 'MP Empleado E', 'tipo': 'Digital', 'es_fiscal': 0},
        {'id_medio': 'MP Usuario F', 'nombre': 'MP Empleado F', 'tipo': 'Digital', 'es_fiscal': 0},
        {'id_medio': 'MP Usuario A', 'nombre': 'MP Socio A', 'tipo': 'Digital', 'es_fiscal': 0},
    ]

    return pd.DataFrame(datos)
