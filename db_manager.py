"""
db_manager.py - Gestión de conexiones a bases de datos (Completado)
Manolo Pajaro Borras - Unisabaneta - Calidad de Software
"""

import psycopg2
from pymongo import MongoClient
import os

PG_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "biblioteca_db"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "Lun@2006"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432"))
}

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")


class DatabaseManager:
    """Gestiona conexiones a PostgreSQL y MongoDB con manejo de errores robusto."""

    def __init__(self):
        self.pg_conn = None
        self.mg_client = None
        self.mg_db = None

    def connect_postgres(self):
        try:
            self.pg_conn = psycopg2.connect(**PG_CONFIG)
            print("[DB] Conexión a PostgreSQL exitosa.")
            return self.pg_conn
        except psycopg2.OperationalError as e:
            print(f"[ERROR] No se pudo conectar a PostgreSQL: {e}")
            raise

    def connect_mongo(self):
        try:
            self.mg_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            self.mg_client.admin.command('ping')
            self.mg_db = self.mg_client['biblioteca_nosql']
            print("[DB] Conexión a MongoDB exitosa.")
            return self.mg_db
        except Exception as e:
            print(f"[ERROR] No se pudo conectar a MongoDB: {e}")
            raise

    def close_all(self):
        if self.pg_conn:
            self.pg_conn.close()
            print("[DB] Conexión PostgreSQL cerrada.")
        if self.mg_client:
            self.mg_client.close()
            print("[DB] Conexión MongoDB cerrada.")

    def execute_pg_query(self, query, params=None):
        """Ejecuta una consulta en PostgreSQL con manejo de errores."""
        try:
            cursor = self.pg_conn.cursor()
            cursor.execute(query, params)
            return cursor
        except psycopg2.Error as e:
            print(f"[ERROR] Fallo en consulta PostgreSQL: {e}")
            self.pg_conn.rollback()
            raise
