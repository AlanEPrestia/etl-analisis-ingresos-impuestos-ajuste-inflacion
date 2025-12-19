"""
Módulo de extracción de datos (EXTRACT).

Responsabilidades:
- Obtener cotización histórica y actual del dólar blue desde una fuente pública.
- Descargar datos de ventas desde Google Sheets mediante credenciales de servicio.

Notas de diseño:
- La cotización histórica se utiliza para neutralizar efectos inflacionarios.
- Se implementa una estrategia híbrida: histórico + valor actual.
- El módulo NO realiza transformaciones de negocio.
"""

import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from datetime import datetime
from .config import FILE_CREDS, NOMBRE_ARCHIVO_SHEET


def obtener_dolar_hibrido():
    """
    Obtiene la cotización histórica y actual del dólar blue.

    Estrategia:
    - Descarga el histórico completo desde una fecha fija (01-01-2022).
    - Consulta el valor del día actual desde un endpoint separado.
    - Unifica ambas fuentes, eliminando duplicados.
    - Completa fechas faltantes mediante forward fill (ffill).

    Retorna:
        DataFrame con columnas:
        - fecha (datetime)
        - cotizacion_blue (float)
    """

    print("💵 [EXTRACT] Consultando Dólar...")

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.ambito.com/"
    }

    df_historico = pd.DataFrame()
    df_hoy = pd.DataFrame()

    # --- HISTÓRICO ---
    try:
        fecha_inicio = "01-01-2022"
        fecha_fin = datetime.now().strftime("%d-%m-%Y")

        url_hist = (
            f"https://mercados.ambito.com//dolar/informal/"
            f"historico-general/{fecha_inicio}/{fecha_fin}"
        )

        resp = requests.get(url_hist, headers=headers, timeout=10)

        if resp.status_code == 200:
            data = resp.json()

            # El endpoint devuelve una matriz donde la primera fila es el header
            df_historico = pd.DataFrame(data[1:], columns=data[0])

            df_historico.rename(
                columns={'Fecha': 'fecha', 'Venta': 'cotizacion_blue'},
                inplace=True
            )

            df_historico['fecha'] = pd.to_datetime(
                df_historico['fecha'],
                format='%d/%m/%Y',
                errors='coerce'
            )

            # Normalización de separadores numéricos
            df_historico['cotizacion_blue'] = (
                df_historico['cotizacion_blue']
                .astype(str)
                .str.replace('.', '')
                .str.replace(',', '.')
                .astype(float)
            )

    except Exception as e:
        print(f"   ⚠️ Falló historial dólar: {e}")

    # --- VALOR ACTUAL ---
    try:
        url_live = "https://mercados.ambito.com//dolar/informal/variacion"
        resp_live = requests.get(url_live, headers=headers, timeout=5)

        if resp_live.status_code == 200:
            data_live = resp_live.json()

            fecha_str = data_live['fecha'].split(' - ')[0]
            valor_str = data_live['venta']

            row_hoy = {
                'fecha': pd.to_datetime(fecha_str, format='%d/%m/%Y'),
                'cotizacion_blue': float(
                    valor_str.replace('.', '').replace(',', '.')
                )
            }

            df_hoy = pd.DataFrame([row_hoy])

    except Exception:
        # El pipeline continúa si falla el valor del día
        pass

    # --- UNIFICACIÓN ---
    df_final = pd.concat([df_historico, df_hoy], ignore_index=True)

    if df_final.empty:
        return pd.DataFrame({'fecha': [], 'cotizacion_blue': []})

    # Elimina duplicados y asegura continuidad temporal
    df_final = (
        df_final
        .drop_duplicates(subset='fecha', keep='last')
        .sort_values('fecha')
    )

    rango = pd.date_range(
        start=df_final['fecha'].min(),
        end=df_final['fecha'].max()
    )

    df_final = (
        df_final
        .set_index('fecha')
        .reindex(rango)
        .ffill()
        .reset_index()
        .rename(columns={'index': 'fecha'})
    )

    return df_final


def obtener_ventas_sheets():
    """
    Descarga los datos de ventas desde Google Sheets.

    Requisitos:
    - Archivo de credenciales de cuenta de servicio.
    - Nombre del archivo configurado en config.py.

    Retorna:
        DataFrame con los datos crudos del Sheet.
    """

    print("🔌 [EXTRACT] Descargando Google Sheets...")

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            FILE_CREDS, scope
        )

        client = gspread.authorize(creds)
        sheet = client.open(NOMBRE_ARCHIVO_SHEET).sheet1
        data = sheet.get_all_records()

        return pd.DataFrame(data)

    except Exception as e:
        print(f"❌ Error Google Sheets: {e}")
        return None
