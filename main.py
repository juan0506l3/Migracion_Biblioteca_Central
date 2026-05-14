import psycopg2
from faker import Faker
import random
import sys
from pymongo import MongoClient
from datetime import datetime
import os

# Evita problemas de encoding en consola
sys.stdout.reconfigure(encoding='utf-8')

# Faker sin caracteres raros
fake = Faker('en_US')

# ---------------------------
# CONEXION
# ---------------------------
def conectar():
    return psycopg2.connect(
        host="localhost",
        database="biblioteca_legacy",
        user="postgres",
        password="l37jjbc0506",
        options='-c client_encoding=utf8'
    )

def limpiar_tablas(conn):
    cursor = conn.cursor()
    print("🧹 Limpiando tablas legacy...")

    try:
        cursor.execute("""
            TRUNCATE TABLE 
                Biblioteca_Data,
                Prestamos_Crudos,
                Inventario_Sedes,
                Reseñas_Usuarios
            RESTART IDENTITY CASCADE;
        """)

        conn.commit()
        print("✅ Tablas limpiadas correctamente")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error limpiando tablas: {e}")

    finally:
        cursor.close()

# ---------------------------
# POBLAR DATOS
# ---------------------------
def poblar_datos(conn):
    cursor = conn.cursor()
    print("Iniciando poblamiento...")

    for i in range(250):
        try:
            print(f"Insertando registro {i+1}/250")

            # Biblioteca_Data
            titulo = fake.sentence(nb_words=4)
            autor = fake.name()
            cat_desc = f"{fake.word()} / {fake.text(max_nb_chars=40)}"
            editorial = fake.company()
            fecha_str = str(fake.date_this_century())

            cursor.execute("""
                INSERT INTO Biblioteca_Data 
                (titulo_libro, autor_nombre, categoria_y_descripcion, editorial_info, fecha_publicacion)
                VALUES (%s, %s, %s, %s, %s)
            """, (titulo, autor, cat_desc, editorial, fecha_str))

            # Prestamos_Crudos
            libros_multi = f"{fake.word()}, {fake.word()}, {fake.word()}"
            cursor.execute("""
                INSERT INTO Prestamos_Crudos 
                (id_prestamo, nombre_usuario, correo_usuario, libros_prestados, fecha_salida, estado_prestamo)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (i, fake.name(), fake.email(), libros_multi, fake.date_this_year(), "Activo"))

            # Reseñas_Usuarios
            cursor.execute("""
                INSERT INTO Reseñas_Usuarios 
                (usuario_id, libro_titulo, comentario, calificacion)
                VALUES (%s, %s, %s, %s)
            """, (random.randint(1, 100), titulo, fake.sentence(), str(random.randint(1, 5))))

            # Inventario_Sedes
            cursor.execute("""
                INSERT INTO Inventario_Sedes 
                (sede_nombre, ubicacion_sede, libro_asociado, cantidad_total)
                VALUES (%s, %s, %s, %s)
            """, (fake.city(), fake.address(), titulo, random.randint(1, 50)))

        except Exception as e:
            print(f"Error en iteracion {i}: {e}")

    conn.commit()
    cursor.close()
    print("Poblamiento completado")

def validar_datos(conn, contexto):
    import json
    import re
    import datetime
    import os

    cursor = conn.cursor()

    print("Iniciando validacion...")

    try:
        # Crear carpeta logs si no existe
        if not os.path.exists("logs"):
            os.makedirs("logs")

        # Cargar JSON
        with open("config/config_calidad.json", encoding="utf-8") as f:
            config = json.load(f)

        reglas = config["reglas_validacion"]

        # para guardar tanto log legacy y normalizado
        modo = "w" if contexto == "legacy" else "a"

        # Abrir archivo log
        with open("logs/errores.log", modo, encoding="utf-8") as log:

            for tabla, lista_reglas in reglas.items():
                print(f"\nValidando tabla: {tabla}")

                for regla in lista_reglas:
                    if regla.get("contexto") != contexto:
                        continue

                    columna = regla["columna"]
                    tipo = regla["tipo_validacion"]

                    print(f" - columna {columna} | Tipo: {tipo}")

                    query = f"SELECT {columna} FROM {tabla}"
                    cursor.execute(query)
                    datos = cursor.fetchall()

                    errores = 0

                    # -------------------------
                    # VALIDACIONES
                    # -------------------------

                    if tipo == "regex":
                        patron = regla["patron"]

                        for valor, in datos:
                            if valor is None or not re.search(patron, str(valor)):
                                errores += 1

                    elif tipo == "rango_numerico":
                        minimo = regla["min"]
                        maximo = regla["max"]

                        for valor, in datos:
                            try:
                                num = int(valor)
                                if num < minimo or num > maximo:
                                    errores += 1
                            except:
                                errores += 1

                    elif tipo == "multivalor":
                        separador = regla["separador"]

                        for valor, in datos:
                            if valor and separador in str(valor):
                                errores += 1

                    elif tipo == "campo_combinado":
                        separador = regla["separador"]

                        for valor, in datos:
                            if valor and separador in str(valor):
                                errores += 1

                    elif tipo == "formato_fecha":
                        for valor, in datos:
                            try:
                                datetime.datetime.strptime(str(valor), "%Y-%m-%d")
                            except:
                                errores += 1

                    # -------------------------
                    # LOG
                    # -------------------------

                    resultado = (
                        f"[VALIDACION] Tabla: {tabla} | Columna: {columna} "
                        f"| Tipo: {tipo} | Errores: {errores}"
                    )

                    print(f"   ❌ Errores encontrados: {errores}")
                    log.write(resultado + "\n")

        print("\nLog generado en logs/errores.log")

    except Exception as e:
        print(f"Error en validacion: {e}")

    finally:
        cursor.close()

def ejecutar_migracion_elt():
    import psycopg2
    import os

    print("\n🔄 Iniciando migración ELT (Legacy → Normalizada)...")

    conn = None
    cursor = None

    try:
        # Conexión a la BD NORMALIZADA
        conn = psycopg2.connect(
            host="localhost",
            database="biblioteca_normalizada",
            user="postgres",
            password="l37jjbc0506"
        )
        cursor = conn.cursor()

        # Ruta del archivo SQL
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ruta_sql = os.path.join(BASE_DIR, "sql", "migracion_elt.sql")

        # Leer script
        with open(ruta_sql, "r", encoding="utf-8") as f:
            sql_script = f.read()

        # Ejecutar script completo
        cursor.execute(sql_script)

        conn.commit()
        print("✅ Migración ELT completada correctamente")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error en migración ELT: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("🔌 Conexión a normalizada cerrada")

def validar_normalizada():
    conn = psycopg2.connect(
        host="localhost",
        database="biblioteca_normalizada",
        user="postgres",
        password="l37jjbc0506"
    )

    validar_datos(conn, "normalizada")
    conn.close()

def limpiar_mongo():
    print("\n🧹 Limpiando base de datos MongoDB...")

    client = MongoClient("mongodb://localhost:27017/")
    db = client["biblioteca_mongo"]

    colecciones = db.list_collection_names()

    for col in colecciones:
        db[col].drop()

    print("✅ MongoDB limpio")
    client.close()

def migrar_a_mongo():
    import psycopg2
    from pymongo import MongoClient

    print("\n🚀 Iniciando migración a MongoDB...")

    # PostgreSQL
    conn = psycopg2.connect(
        host="localhost",
        database="biblioteca_normalizada",
        user="postgres",
        password="l37jjbc0506"
    )
    cursor = conn.cursor()

    # MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["biblioteca_mongo"]

    # -------------------------
    # LIBROS (con embebidos)
    # -------------------------
    cursor.execute("""
        SELECT l.id_libro, l.titulo, l.fecha_publicacion,
               e.nombre
        FROM Libros l
        JOIN Editoriales e ON l.id_editorial = e.id_editorial
    """)

    libros = cursor.fetchall()

    for libro in libros:
        id_libro, titulo, fecha, editorial = libro

        # autores
        cursor.execute("""
            SELECT a.nombre
            FROM Libro_Autor la
            JOIN Autores a ON la.id_autor = a.id_autor
            WHERE la.id_libro = %s
        """, (id_libro,))
        autores = [{"nombre": a[0]} for a in cursor.fetchall()]

        # categorias
        cursor.execute("""
            SELECT c.nombre, c.descripcion
            FROM Libro_Categoria lc
            JOIN Categorias c ON lc.id_categoria = c.id_categoria
            WHERE lc.id_libro = %s
        """, (id_libro,))
        categorias = [
            {"nombre": c[0], "descripcion": c[1]}
            for c in cursor.fetchall()
        ]

        doc = {
            "_id": id_libro,
            "titulo": titulo,
            "fecha": datetime.combine(fecha, datetime.min.time()),
            "editorial": {"nombre": editorial},
            "autores": autores,
            "categorias": categorias
        }

        db.libros.insert_one(doc)

    print("✅ Libros migrados")

    # -------------------------
    # USUARIOS
    # -------------------------
    cursor.execute("SELECT id_usuario, nombre, correo FROM Usuarios")

    for u in cursor.fetchall():
        db.usuarios.insert_one({
            "_id": u[0],
            "nombre": u[1],
            "correo": u[2]
        })

    print("✅ Usuarios migrados")

    # -------------------------
    # PRESTAMOS
    # -------------------------
    cursor.execute("""
        SELECT p.id_prestamo, p.fecha_salida, p.estado,
               u.nombre, u.correo
        FROM Prestamos p
        JOIN Usuarios u ON p.id_usuario = u.id_usuario
    """)

    prestamos = cursor.fetchall()

    for p in prestamos:
        id_prestamo, fecha, estado, nombre, correo = p

        # libros del préstamo
        cursor.execute("""
            SELECT l.titulo
            FROM Prestamo_Libro pl
            JOIN Libros l ON pl.id_libro = l.id_libro
            WHERE pl.id_prestamo = %s
        """, (id_prestamo,))

        libros = [{"titulo": l[0]} for l in cursor.fetchall()]

        doc = {
            "_id": id_prestamo,
            "fecha": datetime.combine(fecha, datetime.min.time()),
            "estado": estado,
            "usuario": {
                "nombre": nombre,
                "correo": correo
            },
            "libros": libros
        }

        db.prestamos.insert_one(doc)

    print("✅ Préstamos migrados")

    # -------------------------
    # INVENTARIO
    # -------------------------
    cursor.execute("""
        SELECT i.cantidad, s.nombre, s.ubicacion, l.id_libro, l.titulo
        FROM Inventario i
        JOIN Sedes s ON i.id_sede = s.id_sede
        JOIN Libros l ON i.id_libro = l.id_libro
    """)

    for i in cursor.fetchall():
        cantidad, sede, ubicacion, id_libro, titulo = i

        doc = {
            "stock": cantidad,
            "sede": {
                "nombre": sede,
                "ubicacion": ubicacion
            },
            "libro": {
                "_id": id_libro,
                "titulo": titulo
            }
        }

        db.inventario.insert_one(doc)

    print("✅ Inventario migrado")

    # cerrar
    cursor.close()
    conn.close()
    client.close()

    print("🎉 Migración a MongoDB completada")

def consulta_libros_mas_prestados():
    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(
            host="localhost",
            database="biblioteca_normalizada",
            user="postgres",
            password="l37jjbc0506"
        )
        cursor = conn.cursor()

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ruta_sql = os.path.join(BASE_DIR, "sql", "vista_libros_mas_prestados.sql")

        with open(ruta_sql, "r", encoding="utf-8") as f:
            statements = f.read().split(";")

        # Ejecutar CREATE OR REPLACE VIEW
        cursor.execute(statements[0])
        conn.commit()
        print("✅ Vista 'vista_libros_mas_prestados' creada correctamente")

        # Ejecutar SELECT y mostrar resultados
        cursor.execute(statements[1])
        resultados = cursor.fetchall()

        print(f"\n📚 Libros más prestados ({len(resultados)} registros):")
        print(f"{'Título':<45} {'Usuario':<25} {'Veces Prestado'}")
        print("-" * 85)

        for titulo, usuario, veces in resultados:
            print(f"{titulo:<45} {usuario:<25} {veces}")

        return resultados

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error en consulta_libros_mas_prestados: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def consulta_top_multas():
    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(
            host="localhost",
            database="biblioteca_normalizada",
            user="postgres",
            password="l37jjbc0506"
        )
        cursor = conn.cursor()

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ruta_sql = os.path.join(BASE_DIR, "sql", "calcular_multa.sql")

        with open(ruta_sql, "r", encoding="utf-8") as f:
            contenido = f.read()

        # Separar por el delimitador seguro entre la función y el SELECT
        partes = contenido.split("-- RUN_QUERY")

        # Crear o reemplazar la función
        cursor.execute(partes[0])
        conn.commit()
        print("✅ Función 'calcular_multa' creada correctamente")

        # Ejecutar SELECT top 10
        cursor.execute(partes[1])
        resultados = cursor.fetchall()

        print(f"\n💸 Top 10 usuarios con mayor multa ({len(resultados)} registros):")
        print(f"{'Usuario':<25} {'Correo':<30} {'ID Préstamo':<13} {'Fecha Salida':<14} {'Días Retraso':<14} {'Multa ($)'}")
        print("-" * 105)

        for nombre, correo, id_prestamo, fecha, dias, multa in resultados:
            print(f"{nombre:<25} {correo:<30} {id_prestamo:<13} {str(fecha):<14} {dias:<14} {multa:,}")

        return resultados

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error en consulta_top_multas: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def ejecutar_log_prestamos():
    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(
            host="localhost",
            database="biblioteca_normalizada",
            user="postgres",
            password="l37jjbc0506"
        )
        cursor = conn.cursor()

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ruta_sql = os.path.join(BASE_DIR, "sql", "generar_log_prestamos.sql")

        with open(ruta_sql, "r", encoding="utf-8") as f:
            partes = f.read().split("-- RUN_QUERY")

        # Crear o reemplazar el procedimiento
        cursor.execute(partes[0])
        conn.commit()
        print("✅ Procedimiento 'generar_log_prestamos' creado correctamente")

        # Ejecutar el CALL
        cursor.execute(partes[1])
        conn.commit()
        print("✅ Log de préstamos generado correctamente en db")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error en ejecutar_log_prestamos: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ---------------------------
# MAIN
# ---------------------------
def main():
    conn = None

    try:
        conn = conectar()
        print("Conexion exitosa a PostgreSQL")

        limpiar_tablas(conn)

        poblar_datos(conn)

        validar_datos(conn, "legacy")

        ejecutar_migracion_elt()

        print("\n📊 Comparando calidad de datos...")

        validar_normalizada()

        limpiar_mongo()

        migrar_a_mongo()

        consulta_libros_mas_prestados()

        print("\n")

        consulta_top_multas()

        print("\n")

        ejecutar_log_prestamos()

        print("\n📊 Verificando datos en Mongo...")

        client = MongoClient("mongodb://localhost:27017/")
        db = client["biblioteca_mongo"]

        print("Libros:", db.libros.count_documents({}))
        print("Usuarios:", db.usuarios.count_documents({}))
        print("Prestamos:", db.prestamos.count_documents({}))
        print("Inventario:", db.inventario.count_documents({}))

        print("\n")

        client.close()

        print("Proceso completado correctamente")

        print("\n")

    except Exception as e:
        print(f"Error general: {e}")

    finally:
        if conn:
            conn.close()
            print("Conexion cerrada")

# ---------------------------
# EJECUCION
# ---------------------------
if __name__ == "__main__":
    main()