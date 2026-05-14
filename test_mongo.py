from pymongo import MongoClient

# Conexión a MongoDB
cliente = MongoClient("mongodb://localhost:27017/")

# Crear base de datos
db = cliente["biblioteca_mongo"]

# Crear colección
coleccion = db["test"]

# Insertar documento
documento = {
    "mensaje": "Mongo funciona",
    "estado": True
}

coleccion.insert_one(documento)

print("✅ Documento insertado correctamente")