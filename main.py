"""
main.py - Orquestador del Pipeline de Calidad de Datos
Taller Final - Calidad de Software
Manolo Pajaro Borras - Unisabaneta

Pipeline completo:
  Fase A: Carga de datos sucios desde Excel
  Fase B: Validación de calidad (reglas del JSON)
  Fase C: Limpieza y normalización (1FN, deduplicación, fuzzy matching)
  Fase D: Migración a MongoDB con Data Masking (SHA-256)
  Fase E: Generación de reporte de calidad
"""

import json
import re
import hashlib
import os
import unicodedata
from datetime import datetime

import difflib

import pandas as pd

# ─────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────
DATA_FILE = "data/Gestion_Biblioteca_Datos_Sucios_Para_Limpiar.xlsx"
CONFIG_FILE = "config/config_calidad.json"
MAPPING_FILE = "config/mapping_mongo.json"
REPORTS_DIR = "reports"

PALABRAS_CANTIDAD = {
    "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}

os.makedirs(REPORTS_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────
def limpiar_texto(valor):
    """Elimina espacios, tabulaciones y normaliza mayúsculas."""
    if pd.isna(valor) or not isinstance(valor, str):
        return valor
    return " ".join(valor.replace("\t", " ").split()).strip().title()


def normalizar_fecha(fecha_str):
    """Convierte fechas en múltiples formatos a YYYY-MM-DD o devuelve None."""
    if pd.isna(fecha_str) or not isinstance(fecha_str, str):
        return None
    fecha_str = fecha_str.strip()
    if fecha_str.lower() in ["sin fecha", "desconocida", "n/a", "na", ""]:
        return None
    formatos = ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y",
                "%Y/%m/%d", "%d.%m.%Y", "%Y"]
    for fmt in formatos:
        try:
            return datetime.strptime(fecha_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_cantidad(valor):
    """Convierte cantidades textuales o numéricas en entero, o None si inválido."""
    if pd.isna(valor):
        return None
    if isinstance(valor, (int, float)):
        val = int(valor)
        return val if val >= 0 else None
    texto = str(valor).strip().lower()
    if texto in PALABRAS_CANTIDAD:
        return PALABRAS_CANTIDAD[texto]
    try:
        val = int(float(texto))
        return val if val >= 0 else None
    except (ValueError, TypeError):
        return None


def normalizar_calificacion(valor):
    """
    Convierte calificaciones en múltiples formatos al entero 1-5.
    Ejemplos: '5/5' -> 5, 'Cinco' -> 5, '2-5' -> None (rango, descartado), '3' -> 3
    """
    PALABRAS_CALIF = {
        "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5
    }
    if pd.isna(valor):
        return None
    texto = str(valor).strip().lower()
    if texto in PALABRAS_CALIF:
        return PALABRAS_CALIF[texto]
    # Formato "X/5" -> tomar numerador
    match_div = re.match(r'^(\d+)/\d+$', texto)
    if match_div:
        num = int(match_div.group(1))
        return num if 1 <= num <= 5 else None
    # Formato rango "X-Y" -> descartar
    if re.match(r'^\d+-\d+$', texto):
        return None
    # Número directo
    try:
        num = int(float(texto))
        return num if 1 <= num <= 5 else None
    except (ValueError, TypeError):
        return None


def hash_correo(correo):
    """Aplica SHA-256 al correo para data masking."""
    if not correo or pd.isna(correo):
        return None
    return hashlib.sha256(str(correo).strip().encode()).hexdigest()


def es_correo_valido(correo):
    """Valida formato de correo electrónico."""
    patron = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(patron, str(correo).strip()))


# ─────────────────────────────────────────────
# CLASE PRINCIPAL
# ─────────────────────────────────────────────
class BibliotecaAutomation:

    def __init__(self):
        self.datos_sucios = {}      # DataFrames originales por hoja
        self.datos_limpios = {}     # DataFrames limpios por hoja
        self.reporte_errores = []   # Lista de errores encontrados
        self.reporte_limpieza = {}  # Estadísticas de limpieza

        with open(CONFIG_FILE, encoding="utf-8") as f:
            self.config = json.load(f)

        with open(MAPPING_FILE, encoding="utf-8") as f:
            self.mapping = json.load(f)

        print("[INIT] Configuración cargada correctamente.\n")

    # ─────────────────────────────────────────
    # FASE A: CARGA DESDE EXCEL
    # ─────────────────────────────────────────
    def cargar_datos_excel(self):
        """Fase A: Carga todas las hojas del Excel en DataFrames."""
        print("=" * 60)
        print("FASE A: Cargando datos sucios desde Excel...")
        print("=" * 60)
        try:
            hojas = pd.read_excel(DATA_FILE, sheet_name=None, dtype=str)
            for nombre, df in hojas.items():
                self.datos_sucios[nombre] = df.copy()
                print(f"  ✓ Hoja '{nombre}': {len(df)} filas, {len(df.columns)} columnas")
            print(f"\n  Total hojas cargadas: {len(self.datos_sucios)}\n")
        except FileNotFoundError:
            print(f"[ERROR] No se encontró el archivo: {DATA_FILE}")
            raise

    # ─────────────────────────────────────────
    # FASE B: VALIDACIÓN DE CALIDAD
    # ─────────────────────────────────────────
    def validar_calidad(self):
        """
        Fase B: Valida los datos crudos contra las reglas del JSON de configuración.
        Registra todos los errores encontrados en self.reporte_errores.
        """
        print("=" * 60)
        print("FASE B: Validando calidad de datos...")
        print("=" * 60)

        reglas = self.config.get("reglas", {})

        # ── Reseñas_Usuarios ──
        df_reseñas = self.datos_sucios.get("Reseñas_Usuarios", pd.DataFrame())
        errores_reseñas = 0
        for idx, fila in df_reseñas.iterrows():
            for regla in reglas.get("Reseñas_Usuarios", []):
                campo = regla["campo"]
                valor = fila.get(campo, None)

                if "tipo" in regla and regla["tipo"] == "numeric":
                    calif = normalizar_calificacion(valor)
                    if calif is None:
                        self.reporte_errores.append({
                            "tabla": "Reseñas_Usuarios",
                            "fila": idx,
                            "campo": campo,
                            "valor": valor,
                            "error": f"Calificación no válida o fuera del rango [{regla['min']}-{regla['max']}]"
                        })
                        errores_reseñas += 1

                if "prohibido" in regla:
                    if pd.isna(valor) or str(valor).strip().lower() in regla["prohibido"]:
                        self.reporte_errores.append({
                            "tabla": "Reseñas_Usuarios",
                            "fila": idx,
                            "campo": campo,
                            "valor": valor,
                            "error": f"Valor prohibido o nulo en campo '{campo}'"
                        })
                        errores_reseñas += 1

        print(f"  ✓ Reseñas_Usuarios: {errores_reseñas} errores detectados")

        # ── Prestamos_Crudos ──
        df_prestamos = self.datos_sucios.get("Prestamos_Crudos", pd.DataFrame())
        errores_prestamos = 0
        for idx, fila in df_prestamos.iterrows():
            for regla in reglas.get("Prestamos_Crudos", []):
                campo = regla["campo"]
                valor = fila.get(campo, None)
                if "pattern" in regla:
                    if pd.isna(valor) or not re.match(regla["pattern"], str(valor).strip()):
                        self.reporte_errores.append({
                            "tabla": "Prestamos_Crudos",
                            "fila": idx,
                            "campo": campo,
                            "valor": valor,
                            "error": f"Formato inválido para campo '{campo}'"
                        })
                        errores_prestamos += 1

        print(f"  ✓ Prestamos_Crudos: {errores_prestamos} errores detectados")

        # ── Inventario_Sedes ──
        df_inv = self.datos_sucios.get("Inventario_Sedes", pd.DataFrame())
        errores_inv = 0
        for idx, fila in df_inv.iterrows():
            for regla in reglas.get("Inventario_Sedes", []):
                campo = regla["campo"]
                valor = fila.get(campo, None)
                if "tipo" in regla and regla["tipo"] == "numeric":
                    cantidad = parse_cantidad(valor)
                    if cantidad is None:
                        self.reporte_errores.append({
                            "tabla": "Inventario_Sedes",
                            "fila": idx,
                            "campo": campo,
                            "valor": valor,
                            "error": "Cantidad inválida, negativa o no numérica"
                        })
                        errores_inv += 1

        print(f"  ✓ Inventario_Sedes: {errores_inv} errores detectados")

        total = len(self.reporte_errores)
        print(f"\n  ► Total errores encontrados en validación: {total}\n")

    # ─────────────────────────────────────────
    # FASE C: LIMPIEZA Y NORMALIZACIÓN
    # ─────────────────────────────────────────
    def limpiar_y_normalizar(self):
        """
        Fase C: Aplica todas las transformaciones de limpieza:
        - Elimina duplicados exactos
        - Limpia ruido de texto (espacios, tabs, mayúsculas)
        - Normaliza fechas a formato ISO
        - Convierte cantidades textuales a numéricas
        - Normaliza calificaciones al rango 1-5
        - Valida y marca correos inválidos
        - Expande la columna libros_prestados (viola 1FN)
        - Aplica Fuzzy Matching para deduplicación inteligente
        """
        print("=" * 60)
        print("FASE C: Limpiando y normalizando datos...")
        print("=" * 60)

        # ── Biblioteca_Data ──
        df = self.datos_sucios["Biblioteca_Data"].copy()
        inicial = len(df)
        df.drop_duplicates(inplace=True)
        df["titulo_libro"] = df["titulo_libro"].apply(limpiar_texto)
        df["autor_nombre"] = df["autor_nombre"].apply(limpiar_texto)
        df["categoria_y_descripcion"] = df["categoria_y_descripcion"].apply(
            lambda x: x.strip() if isinstance(x, str) else x
        )
        df["editorial_info"] = df["editorial_info"].apply(
            lambda x: " ".join(x.replace("\t", " ").split()).strip() if isinstance(x, str) else x
        )
        df["fecha_publicacion"] = df["fecha_publicacion"].apply(normalizar_fecha)
        df.dropna(subset=["titulo_libro", "autor_nombre"], inplace=True)
        df.reset_index(drop=True, inplace=True)
        self.datos_limpios["Biblioteca_Data"] = df
        self.reporte_limpieza["Biblioteca_Data"] = {
            "filas_originales": inicial,
            "filas_limpias": len(df),
            "eliminadas": inicial - len(df)
        }
        print(f"  ✓ Biblioteca_Data: {inicial} → {len(df)} filas ({inicial - len(df)} eliminadas)")

        # ── Fuzzy Matching en Biblioteca_Data ──
        df = self._aplicar_fuzzy_matching(df, "titulo_libro", "autor_nombre")
        self.datos_limpios["Biblioteca_Data"] = df
        print(f"  ✓ Fuzzy Matching aplicado. Registros tras deduplicación: {len(df)}")

        # ── Prestamos_Crudos ──
        df_p = self.datos_sucios["Prestamos_Crudos"].copy()
        inicial = len(df_p)
        df_p.drop_duplicates(inplace=True)
        df_p["nombre_usuario"] = df_p["nombre_usuario"].apply(limpiar_texto)
        df_p["correo_usuario"] = df_p["correo_usuario"].apply(
            lambda x: x.strip() if isinstance(x, str) else x
        )
        df_p["correo_valido"] = df_p["correo_usuario"].apply(
            lambda x: es_correo_valido(x) if not pd.isna(x) else False
        )
        df_p["fecha_salida"] = df_p["fecha_salida"].apply(normalizar_fecha)
        df_p["estado_prestamo"] = df_p["estado_prestamo"].apply(limpiar_texto)

        # Expandir libros_prestados (violación 1FN): una fila por libro
        filas_expandidas = []
        for _, fila in df_p.iterrows():
            libros_raw = fila.get("libros_prestados", "")
            if pd.isna(libros_raw) or str(libros_raw).strip() == "":
                filas_expandidas.append(fila.to_dict())
            else:
                libros = [l.strip() for l in str(libros_raw).split(",") if l.strip()]
                for libro in libros:
                    nueva_fila = fila.to_dict()
                    nueva_fila["libro_prestado_individual"] = libro
                    filas_expandidas.append(nueva_fila)

        df_p_expandido = pd.DataFrame(filas_expandidas)
        df_p_expandido.reset_index(drop=True, inplace=True)
        self.datos_limpios["Prestamos_Crudos"] = df_p_expandido
        self.reporte_limpieza["Prestamos_Crudos"] = {
            "filas_originales": inicial,
            "filas_limpias": len(df_p_expandido),
            "correos_invalidos": int((~df_p["correo_valido"]).sum())
        }
        print(f"  ✓ Prestamos_Crudos: {inicial} → {len(df_p_expandido)} filas (expandido por libros)")

        # ── Inventario_Sedes ──
        df_i = self.datos_sucios["Inventario_Sedes"].copy()
        inicial = len(df_i)
        df_i.drop_duplicates(inplace=True)
        df_i["sede_nombre"] = df_i["sede_nombre"].apply(limpiar_texto)
        df_i["ubicacion_sede"] = df_i["ubicacion_sede"].apply(limpiar_texto)
        df_i["libro_asociado"] = df_i["libro_asociado"].apply(limpiar_texto)
        df_i["cantidad_total"] = df_i["cantidad_total"].apply(parse_cantidad)
        df_i.dropna(subset=["cantidad_total"], inplace=True)
        df_i.reset_index(drop=True, inplace=True)
        self.datos_limpios["Inventario_Sedes"] = df_i
        self.reporte_limpieza["Inventario_Sedes"] = {
            "filas_originales": inicial,
            "filas_limpias": len(df_i),
            "eliminadas": inicial - len(df_i)
        }
        print(f"  ✓ Inventario_Sedes: {inicial} → {len(df_i)} filas")

        # ── Reseñas_Usuarios ──
        df_r = self.datos_sucios["Reseñas_Usuarios"].copy()
        inicial = len(df_r)
        df_r.drop_duplicates(inplace=True)
        df_r["libro_titulo"] = df_r["libro_titulo"].apply(limpiar_texto)
        df_r["comentario"] = df_r["comentario"].apply(limpiar_texto)
        df_r["calificacion"] = df_r["calificacion"].apply(normalizar_calificacion)
        df_r = df_r[
            df_r["usuario_id"].notna() &
            (df_r["usuario_id"].astype(str).str.strip().str.lower() != "usuario_desconocido")
        ]
        df_r = df_r[df_r["calificacion"].notna()]
        df_r = df_r[
            df_r["comentario"].notna() &
            (~df_r["comentario"].str.lower().isin(["nulo", "sin comentario"]))
        ]
        df_r.reset_index(drop=True, inplace=True)
        self.datos_limpios["Reseñas_Usuarios"] = df_r
        self.reporte_limpieza["Reseñas_Usuarios"] = {
            "filas_originales": inicial,
            "filas_limpias": len(df_r),
            "eliminadas": inicial - len(df_r)
        }
        print(f"  ✓ Reseñas_Usuarios: {inicial} → {len(df_r)} filas\n")

    def _aplicar_fuzzy_matching(self, df, campo_titulo, campo_autor):
        """
        Fuzzy Matching: detecta registros con títulos y autores similares
        (supera umbral de similitud) y conserva solo el 'Registro Maestro'
        (el primero que aparece).
        """
        umbral = self.config["fuzzy_matching"]["umbral_similitud"]
        indices_a_eliminar = set()
        filas = df[[campo_titulo, campo_autor]].fillna("").values.tolist()
        n = len(filas)

        for i in range(n):
            if i in indices_a_eliminar:
                continue
            for j in range(i + 1, n):
                if j in indices_a_eliminar:
                    continue
                sim_titulo = difflib.SequenceMatcher(None, " ".join(sorted(filas[i][0].lower().split())), " ".join(sorted(filas[j][0].lower().split()))).ratio() * 100
                sim_autor = difflib.SequenceMatcher(None, " ".join(sorted(filas[i][1].lower().split())), " ".join(sorted(filas[j][1].lower().split()))).ratio() * 100
                if sim_titulo >= umbral and sim_autor >= umbral:
                    indices_a_eliminar.add(j)

        df_dedup = df.drop(index=list(indices_a_eliminar)).reset_index(drop=True)
        print(f"    Fuzzy: {len(indices_a_eliminar)} duplicados semánticos eliminados (umbral={umbral}%)")
        return df_dedup

    # ─────────────────────────────────────────
    # FASE D: MIGRACIÓN A MONGODB
    # ─────────────────────────────────────────
    def migrar_a_nosql(self, mg_db=None):
        """
        Fase D: Migra los datos limpios a MongoDB aplicando:
        - Mapeo de campos desde mapping_mongo.json
        - Data Masking (SHA-256) en correos
        - Inserción por lotes usando insert_many
        """
        print("=" * 60)
        print("FASE D: Migrando datos limpios a MongoDB...")
        print("=" * 60)

        if mg_db is None:
            print("  [INFO] No hay conexión a MongoDB. Exportando a JSON simulado...")
            self._exportar_json_simulado()
            return

        colecciones = self.mapping["colecciones"]

        # ── Libros ──
        df_lib = self.datos_limpios.get("Biblioteca_Data", pd.DataFrame())
        docs_libros = df_lib.where(pd.notnull(df_lib), None).to_dict(orient="records")
        if docs_libros:
            mg_db["libros"].drop()
            mg_db["libros"].insert_many(docs_libros)
            print(f"  ✓ Colección 'libros': {len(docs_libros)} documentos insertados")

        # ── Préstamos con Data Masking ──
        df_pres = self.datos_limpios.get("Prestamos_Crudos", pd.DataFrame()).copy()
        df_pres["correo_usuario"] = df_pres["correo_usuario"].apply(hash_correo)
        docs_prestamos = df_pres.where(pd.notnull(df_pres), None).to_dict(orient="records")
        if docs_prestamos:
            mg_db["prestamos"].drop()
            mg_db["prestamos"].insert_many(docs_prestamos)
            print(f"  ✓ Colección 'prestamos': {len(docs_prestamos)} documentos (correos enmascarados con SHA-256)")

        # ── Inventario ──
        df_inv = self.datos_limpios.get("Inventario_Sedes", pd.DataFrame())
        docs_inv = df_inv.where(pd.notnull(df_inv), None).to_dict(orient="records")
        if docs_inv:
            mg_db["inventario"].drop()
            mg_db["inventario"].insert_many(docs_inv)
            print(f"  ✓ Colección 'inventario': {len(docs_inv)} documentos insertados")

        # ── Reseñas ──
        df_res = self.datos_limpios.get("Reseñas_Usuarios", pd.DataFrame())
        docs_res = df_res.where(pd.notnull(df_res), None).to_dict(orient="records")
        if docs_res:
            mg_db["reseñas"].drop()
            mg_db["reseñas"].insert_many(docs_res)
            print(f"  ✓ Colección 'reseñas': {len(docs_res)} documentos insertados")

        print()

    def _exportar_json_simulado(self):
        """Exporta los datos limpios a JSON cuando MongoDB no está disponible."""
        import json as _json

        for nombre, df in self.datos_limpios.items():
            df_export = df.copy()
            # Aplicar masking al correo si aplica
            if "correo_usuario" in df_export.columns:
                df_export["correo_usuario"] = df_export["correo_usuario"].apply(hash_correo)
            ruta = os.path.join(REPORTS_DIR, f"{nombre.lower().replace(' ', '_')}_limpio.json")
            registros = df_export.where(pd.notnull(df_export), None).to_dict(orient="records")
            with open(ruta, "w", encoding="utf-8") as f:
                _json.dump(registros, f, ensure_ascii=False, indent=2, default=str)
            print(f"  ✓ {nombre}: {len(registros)} registros → {ruta}")
        print()

    # ─────────────────────────────────────────
    # FASE E: GENERACIÓN DE REPORTE
    # ─────────────────────────────────────────
    def generar_reporte(self):
        """Fase E: Genera un reporte completo de calidad en texto y CSV."""
        print("=" * 60)
        print("FASE E: Generando reporte de calidad...")
        print("=" * 60)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_txt = os.path.join(REPORTS_DIR, f"reporte_calidad_{timestamp}.txt")
        ruta_csv = os.path.join(REPORTS_DIR, f"errores_validacion_{timestamp}.csv")

        # Guardar errores de validación en CSV
        if self.reporte_errores:
            df_errores = pd.DataFrame(self.reporte_errores)
            df_errores.to_csv(ruta_csv, index=False, encoding="utf-8-sig")
            print(f"  ✓ Errores de validación exportados → {ruta_csv}")

        # Reporte de texto
        lineas = [
            "=" * 60,
            "   REPORTE DE CALIDAD - GESTIÓN BIBLIOTECA",
            f"   Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
            "RESUMEN DE LIMPIEZA POR TABLA",
            "-" * 40
        ]
        for tabla, stats in self.reporte_limpieza.items():
            lineas.append(f"\n  ► {tabla}:")
            for k, v in stats.items():
                lineas.append(f"      {k}: {v}")

        lineas += [
            "",
            "-" * 40,
            f"  Total errores de validación detectados: {len(self.reporte_errores)}",
            "",
            "PROCESOS APLICADOS",
            "-" * 40,
            "  [✓] Eliminación de duplicados exactos",
            "  [✓] Limpieza de ruido en texto (espacios, tabs, mayúsculas)",
            "  [✓] Normalización de fechas (múltiples formatos → ISO 8601)",
            "  [✓] Conversión de cantidades textuales a numéricas",
            "  [✓] Normalización de calificaciones (rango 1-5)",
            "  [✓] Validación de correos electrónicos (regex)",
            "  [✓] Normalización 1FN: expansión de libros_prestados",
            f"  [✓] Fuzzy Matching (umbral {self.config['fuzzy_matching']['umbral_similitud']}%)",
            "  [✓] Data Masking: correos enmascarados con SHA-256",
            "=" * 60
        ]

        with open(ruta_txt, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas))

        print(f"  ✓ Reporte de calidad exportado → {ruta_txt}\n")
        print("\n".join(lineas))

    # ─────────────────────────────────────────
    # PIPELINE PRINCIPAL
    # ─────────────────────────────────────────
    def ejecutar_pipeline(self):
        """Ejecuta el pipeline completo con manejo de errores."""
        try:
            self.cargar_datos_excel()
        except Exception as e:
            print(f"[FALLO] Fase A: {e}")
            return

        try:
            self.validar_calidad()
        except Exception as e:
            print(f"[FALLO] Fase B: {e}")

        try:
            self.limpiar_y_normalizar()
        except Exception as e:
            print(f"[FALLO] Fase C: {e}")
            return

        # Intentar conexión a MongoDB (opcional)
        mg_db = None
        try:
            from db_manager import DatabaseManager
            db_manager = DatabaseManager()
            mg_db = db_manager.connect_mongo()
        except Exception:
            print("  [INFO] MongoDB no disponible. Se usará exportación JSON local.\n")

        try:
            self.migrar_a_nosql(mg_db=mg_db)
        except Exception as e:
            print(f"[FALLO] Fase D: {e}")

        try:
            self.generar_reporte()
        except Exception as e:
            print(f"[FALLO] Fase E: {e}")

        if mg_db is not None:
            try:
                db_manager.close_all()
            except Exception:
                pass


# ─────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = BibliotecaAutomation()
    app.ejecutar_pipeline()
