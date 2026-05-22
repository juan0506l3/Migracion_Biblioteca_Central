# Migración Biblioteca Central

Este proyecto orquesta un pipeline de calidad de datos para una biblioteca, desde la ingestión de datos sucios en Excel hasta la migración a MongoDB y la generación de reportes de calidad.

## 📌 Objetivo

Validar, limpiar, normalizar y migrar los datos de una biblioteca escolar o institucional.
El pipeline está diseñado para:
- cargar datos sucios desde un archivo Excel con múltiples hojas,
- aplicar reglas de calidad definidas en JSON,
- limpiar texto, normalizar fechas y convertir formatos heterogéneos,
- expandir datos para cumplir 1FN,
- realizar deduplicación inteligente con fuzzy matching,
- aplicar data masking a correos sensibles,
- migrar datos limpios a MongoDB,
- generar reportes de calidad y errores.

## 📁 Estructura del proyecto

```
Migracion_Biblioteca_Central/
  ├── config/
  │   ├── config_calidad.json       # Reglas de validación y parámetros de fuzzy matching
  │   └── mapping_mongo.json        # Mapeo de tablas a colecciones MongoDB
  ├── data/
  │   ├── Gestion_Biblioteca_Datos_Sucios_Para_Limpiar.xlsx  # Datos de entrada sucios
  │   └── ...                       # Otros datos de ejemplo o archivos usados internamente
  ├── reports/
  │   ├── *.json                    # Exportaciones de datos limpios cuando MongoDB no está disponible
  │   ├── *.csv                     # Errores de validación
  │   └── *.txt                     # Reportes de calidad generados
  ├── sql/
  │   └── schema_sucio.sql          # Esquema SQL inicial de PostgreSQL usado en Docker
  ├── tests/
  │   └── test_pipeline.py         # Pruebas unitarias de funciones de limpieza y validación
  ├── db_manager.py                # Gestión de conexiones PostgreSQL y MongoDB
  ├── docker-compose.yml           # Definición de servicios Docker para PostgreSQL, MongoDB y la app
  ├── Dockerfile                   # Imagen Docker para ejecutar el pipeline Python
  ├── main.py                      # Orquestador principal del pipeline
  └── requirements.txt             # Dependencias Python
```

## 🚀 Flujo del pipeline

El pipeline principal se ejecuta desde `main.py` y sigue estas fases:

1. **Fase A - Carga de datos sucios desde Excel**
   - Lee todas las hojas del archivo `data/Gestion_Biblioteca_Datos_Sucios_Para_Limpiar.xlsx`.
   - Guarda cada hoja como un DataFrame en `self.datos_sucios`.

2. **Fase B - Validación de calidad**
   - Usa `config/config_calidad.json` para validar campos según reglas:
     - `Reseñas_Usuarios`: calificaciones válidas y comentarios prohibidos.
     - `Prestamos_Crudos`: correos con patrón válido.
     - `Inventario_Sedes`: cantidades numéricas no negativas.
     - `Biblioteca_Data`: campos requeridos.
   - Genera un listado de errores en `self.reporte_errores`.

3. **Fase C - Limpieza y normalización**
   - Elimina duplicados exactos.
   - Normaliza texto con `limpiar_texto`.
   - Convierte fechas a formato `YYYY-MM-DD`.
   - Convierte palabras numéricas y strings a enteros.
   - Normaliza calificaciones al rango `1-5`.
   - Valida correos y marca los no válidos.
   - Expande `libros_prestados` para cumplir 1FN.
   - Aplica `fuzzy matching` a `Biblioteca_Data` para eliminar duplicados semánticos.
   - Guarda resultados en `self.datos_limpios`.

4. **Fase D - Migración a MongoDB**
   - Usa `config/mapping_mongo.json` para mapear tablas a colecciones.
   - Inserta documentos en MongoDB para:
     - `libros`
     - `prestamos`
     - `inventario`
     - `reseñas`
   - Aplica hashing SHA-256 a `correo_usuario` antes de insertar.
   - Si MongoDB no está disponible, exporta JSON de los datos limpios en `reports/`.

5. **Fase E - Generación de reporte de calidad**
   - Crea un reporte de texto con estadísticas de limpieza y totales de errores.
   - Exporta errores de validación a CSV.
   - Guarda reportes en `reports/`.

## 🧩 Configuración principal

### `config/config_calidad.json`

Contiene reglas de validación, umbral de fuzzy matching y configuración de data masking.

- `reglas` define por hoja:
  - campos requeridos,
  - patrones regex,
  - tipos numéricos y valores prohibidos.
- `fuzzy_matching` define el umbral de similitud y campos comparados.
- `data_masking` define qué campos se enmascaran y con qué método.

### `config/mapping_mongo.json`

Describe cómo se traducen las tablas del DataFrame a colecciones MongoDB.
Cada colección define:
- `fuente_tabla`: la hoja de Excel original,
- `campos`: el mapeo de nombres de campo de origen a destino.

## ⚙️ Instalación y ejecución local

### Requisitos previos

- Python 3.11+
- Docker y Docker Compose (opcional para la ejecución en contenedores)
- `pip`

### Instalación de dependencias

```bash
cd "c:/Proyectos propios/Proyectos python/Migración biblioteca/Migracion_Biblioteca_Central"
pip install -r requirements.txt
```

### Ejecutar el pipeline localmente

```bash
python main.py
```

El proceso genera archivos en `reports/`.

## 🐳 Ejecución con Docker

### Construir y arrancar con Docker Compose

```bash
docker compose up --build
```

### Qué servicios levanta

- `postgres`: PostgreSQL con un esquema inicial definido en `sql/schema_sucio.sql`.
- `mongodb`: MongoDB para almacenar los datos migrados.
- `app_python`: ejecuta `main.py` dentro de un contenedor Python.

> Nota: el pipeline actual de `main.py` solo conecta con MongoDB. PostgreSQL está definido como servicio en Docker Compose pero no se usa activamente en el flujo principal.

### Variables de entorno usadas

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `MONGO_URI`

> Nota: Docker Compose monta `./reports` y `./data` en el contenedor para persistencia y acceso a los datos.

## 🧪 Pruebas

### Ejecutar pruebas unitarias con pytest

```bash
pytest tests/ -v
```

### Ejecutar con unittest estándar

```bash
python -m unittest discover tests/ -v
```

## 🔧 Archivos importantes

- `main.py`: controlador del flujo completo del pipeline.
- `db_manager.py`: conexión y manejo de PostgreSQL y MongoDB. Nota: la conexión PostgreSQL está disponible, pero `main.py` solo utiliza MongoDB en el flujo actual.
- `requirements.txt`: dependencias Python necesarias.
- `docker-compose.yml`: servicios Docker para la app y bases de datos.
- `Dockerfile`: imagen para ejecutar el pipeline en Docker.
- `config/config_calidad.json`: reglas de validación y parámetros.
- `config/mapping_mongo.json`: mapeo de tablas a colecciones MongoDB.

## 💡 Consideraciones clave

- Si `MongoDB` no está accesible, el pipeline no falla: en su lugar exporta JSON limpio a `reports/`.
- El reporte de calidad guarda tanto detalle de errores como estadísticas de limpieza.
- El proceso de `fuzzy matching` usa `difflib.SequenceMatcher` para detectar duplicados semánticos.
- El pipeline aplica `data masking` en correos sensibles con SHA-256 para proteger datos personales.

## 📌 Recomendaciones

- Actualizar `config/config_calidad.json` si se requieren nuevas reglas de validación.
- Revisar `config/mapping_mongo.json` cuando cambie la estructura objetivo de MongoDB.
- Limpiar la carpeta `reports/` entre ejecuciones si desea evitar acumulación de archivos antiguos.

---

### Autor
Proyecto desarrollado como parte del taller de Calidad de Software.
