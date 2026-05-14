
-- TABLA 1: Violación de 1FN (Campo combinado y tipo de dato incorrecto)
CREATE TABLE Biblioteca_Data (
    id_registro SERIAL PRIMARY KEY,
    titulo_libro VARCHAR(255),
    autor_nombre VARCHAR(255),
    categoria_y_descripcion TEXT, -- Error: Campo combinado (Viola 1FN) [cite: 31]
    editorial_info VARCHAR(255),
    fecha_publicacion VARCHAR(50) -- Error: Debería ser DATE [cite: 33]
);

-- TABLA 2: Violación de 1FN (Lista multivalorada)
CREATE TABLE Prestamos_Crudos (
    id_prestamo INT,
    nombre_usuario VARCHAR(255),
    correo_usuario VARCHAR(255),
    libros_prestados TEXT, -- Error: Lista separada por comas [cite: 39]
    fecha_salida DATE,
    estado_prestamo VARCHAR(20)
);

-- TABLA 3: Redundancia y falta de integridad referencial
CREATE TABLE Inventario_Sedes (
    sede_nombre VARCHAR(100),
    ubicacion_sede VARCHAR(255),
    libro_asociado VARCHAR(255), -- Error: Sin FK explícita [cite: 45]
    cantidad_total INT
);

-- TABLA 4: Tipo de dato inconsistente
CREATE TABLE Reseñas_Usuarios (
    usuario_id INT,
    libro_titulo VARCHAR(255),
    comentario TEXT,
    calificacion VARCHAR(10) -- Error: Debería ser numérico (1-5) [cite: 52]
);