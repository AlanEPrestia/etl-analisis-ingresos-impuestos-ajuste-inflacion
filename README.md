# Proyecto ETL – Análisis de Ingresos con Ajuste por Inflación (Argentina)

## 📌 Descripción general

Este proyecto implementa un **pipeline ETL completo** orientado al **análisis económico y fiscal de los ingresos** de un negocio en el contexto argentino, caracterizado por **procesos inflacionarios sostenidos**.

El principal objetivo es **analizar los ingresos reales del negocio**, considerando:

* su **evolución a lo largo del tiempo**, ajustada por inflación mediante la **cotización histórica del dólar**
* la **composición de los ingresos** según medio de pago y condición fiscal
* la **proporcion de ingresos registrados y no registrados**
* el **impacto de los componentes impositivos** sobre los montos brutos y netos

De esta forma, el proyecto permite evaluar no solo cuánto se factura, sino **cómo se compone ese ingreso, cómo evoluciona en términos reales y qué proporción se destina al pago de impuestos**.

El proyecto fue desarrollado en el marco de un **bootcamp de Data Analytics**, con un enfoque deliberadamente más cercano a un **entorno profesional / productivo**.


## 🎯 Problema de negocio

Los datos de ventas se recolectaron a lo largo de varios años mediante carga manual en Google Sheets. Esto genera múltiples desafíos:

* Valores nominales no comparables entre años debido a la inflación
* Montos escritos en texto libre (mezcla de números, monedas y comentarios)
* Registro de ventas tanto en ARS como en USD
* Necesidad de distinguir ingresos fiscales y no fiscales, así como su impacto impositivo

Analizar estos datos sin un proceso de limpieza, estandarización y auditoría conduce a conclusiones incompletas o distorsionadas, especialmente en contextos de alta inflación.

---

## 💡 Solución propuesta

Se diseñó un **pipeline ETL modular** que:

1. Extrae datos de ventas desde Google Sheets
2. Extrae la cotización histórica del dólar desde una API externa
3. Limpia y normaliza montos monetarios (incluyendo texto libre)
4. Convierte valores a una base comparable en el tiempo
5. Calcula impuestos según reglas de negocio
6. Modela los datos en un **esquema tipo estrella (Star Schema)**
7. Carga la información en PostgreSQL para su análisis posterior en herramientas BI

---

## 🧱 Arquitectura del proyecto

```
Google Sheets + API Dólar
        ↓
     EXTRACT
        ↓
    TRANSFORM
        ↓
PostgreSQL (Docker)
        ↓
   Power BI
```

---

## 🗂️ Estructura del proyecto

```
.
├── src/
│   ├── extraction.py      # Extracción de datos (Sheets + API Dólar)
│   ├── transformation.py  # Limpieza, normalización y reglas de negocio
│   ├── loading.py         # Carga a PostgreSQL
│   ├── config.py          # Configuración general
│   └── __init__.py
│
│── docker/
│   └── docker-compose.yml # PostgreSQL (Docker)
│── reports/
│   └── 
├── main.py                # Orquestador del pipeline ETL 
├── requirements.txt       # Dependencias del proyecto
├── pyproject.toml         # Metadata del proyecto
├── README.md
└── .gitignore
```

---

## 🗃️ Modelo de datos

El modelo sigue un enfoque **dimensional (Star Schema)**:

### 📊 Tabla de hechos

* **fact_ingresos**: registra los ingresos normalizados y auditados

### 📐 Dimensiones

* **dim_calendario**: análisis temporal
* **dim_medios_pago**: clasificación por medio de cobro y fiscalidad
* **dim_cotizacion**: cotización histórica del dólar

Este modelo facilita el análisis posterior en herramientas de BI.

---

## 🛠️ Tecnologías utilizadas

* **Python 3.10+**
* **Pandas / NumPy**
* **Google Sheets API (gspread)**
* **Requests (API externa)**
* **PostgreSQL**
* **SQLAlchemy**
* **Docker & Docker Compose**
* **Power BI**

---

## 🚀 Cómo levantar el proyecto

### 1️⃣ Clonar el repositorio

```bash
git clone <https://github.com/AlanEPrestia/etl-analisis-ingresos-impuestos-ajuste-inflacion.git>
cd proyecto-bootcamp-devlights
```

---

### 2️⃣ Crear y activar el entorno virtual (uv)

```bash
uv venv
uv pip install -r requirements.txt
```

---

### 3️⃣ Configuración de acceso a Google Sheets

El pipeline obtiene los datos desde **Google Sheets** mediante la API oficial de Google,
utilizando un **Service Account**.

Para ejecutar el proyecto en un entorno local es obligatorio contar con credenciales válidas.
Este repositorio **no incluye credenciales reales**, ya que se trabaja con datos de un cliente
y con información sensible.

#### Tipo de credenciales requeridas

El proyecto espera un archivo de credenciales con las siguientes características:

- **Tipo:** Google Cloud Service Account  
- **Formato:** JSON  
- **Permisos mínimos:** acceso de lectura al Google Sheet  
- **Archivo:** `credentials.json` (no versionado)

El Google Sheet utilizado como fuente de datos debe estar compartido con el email
asociado al Service Account.

#### Configuración local

La ubicación del archivo de credenciales debe definirse mediante una variable de entorno:

```bash
GOOGLE_APPLICATION_CREDENTIALS=/ruta/absoluta/credentials.json



### 4️⃣ Levantar la infraestructura con Docker

```bash
docker-compose up -d
```

Servicios disponibles:

* PostgreSQL → `localhost:5440`

---

### 5️⃣ Ejecutar el pipeline ETL

```bash
python main.py
```

Al finalizar, las tablas quedarán cargadas en PostgreSQL.

---

## 📈 Análisis y visualización

Los datos cargados en PostgreSQL se analizan utilizando **Power BI**, conectándose directamente a la base de datos.

El modelo dimensional permite:

* Análisis temporal
* Comparación real de ingresos ajustados por inflación
* Segmentación por medio de pago
* Análisis de ingresos registrados vs no registrados
* Análisis de impuestos, montos netos y rentabilidad

---

## 🧠 Consideraciones analíticas

* La cotización histórica del dólar se utiliza como **referencia temporal** para mitigar distorsiones inflacionarias
* La limpieza de texto libre incluye **etiquetas de auditoría** para trazabilidad
* El pipeline está diseñado para ser **escalable y automatizable**

---

## 👤 Autor

**Alan Prestia**
Data Analyst / Instructor de Programación
📧 [alaneprestia@gmail.com](mailto:alaneprestia@gmail.com)

---

## ⚠️ Nota

Este proyecto fue desarrollado con fines educativos en el marco de un bootcamp, utilizando **datos reales de un cliente**, tratados con criterios de confidencialidad y anonimización. 

## Contexto del proyecto

Este proyecto fue desarrollado siguiendo **requerimientos formales de un cliente**,
trabajando con **datos reales de operación**.  
Por este motivo, el repositorio no incluye información sensible ni credenciales reales,
y ciertos aspectos del sistema fueron diseñados priorizando confidencialidad,
trazabilidad y consistencia de los datos.

El objetivo principal del pipeline es **construir una base analítica confiable**
a partir de fuentes no estructuradas, aplicando criterios de limpieza,
auditoría y modelado orientado a Business Intelligence.

## Alcance y supuestos actuales

- El pipeline se ejecuta en modo **batch**.
- La ingesta de datos es **completa** en cada ejecución.
- No se implementa aún una tabla de auditoría persistente del proceso.
- Las transformaciones responden a reglas de negocio vigentes al momento
  del desarrollo del proyecto.

## Próximos pasos (Roadmap)

Como evolución natural del sistema, se consideran los siguientes pasos:

- Implementación de **ingesta incremental** basada en marcas temporales.
- Incorporación de una **tabla de auditoría** para registrar ejecuciones,
  volúmenes procesados y eventos relevantes.
- Optimización del proceso de carga para escenarios de mayor volumen.




