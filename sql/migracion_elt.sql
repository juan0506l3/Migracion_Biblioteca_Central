-- DESACTIVAR TRIGGERS
ALTER TABLE Prestamo_Libro DISABLE TRIGGER ALL;

-- ========================================
-- LIMPIEZA TOTAL
-- ========================================
TRUNCATE TABLE 
    Prestamo_Libro,
    Libro_Autor,
    Libro_Categoria,
    Inventario,
    Reseñas,
    Prestamos,
    Usuarios,
    Categorias,
    Autores,
    Libros,
    Editoriales,
    Sedes,
    log_prestamos
RESTART IDENTITY CASCADE;

-- ========================================
-- 1. EXTENSIÓN
-- ========================================
CREATE EXTENSION IF NOT EXISTS dblink;

-- ========================================
-- 2. EDITORIALES
-- ========================================
INSERT INTO Editoriales (nombre)
SELECT DISTINCT editorial_info
FROM dblink(
    'dbname=biblioteca_legacy user=postgres password=l37jjbc0506',
    'SELECT editorial_info FROM Biblioteca_Data'
) AS t(editorial_info TEXT);

-- ========================================
-- 3. LIBROS
-- ========================================
INSERT INTO Libros (titulo, fecha_publicacion, id_editorial)
SELECT 
    b.titulo,
    b.fecha::DATE,
    e.id_editorial
FROM dblink(
    'dbname=biblioteca_legacy user=postgres password=l37jjbc0506',
    'SELECT titulo_libro, fecha_publicacion, editorial_info FROM Biblioteca_Data'
) AS b(titulo TEXT, fecha TEXT, editorial TEXT)
JOIN Editoriales e
ON TRIM(b.editorial) = TRIM(e.nombre);

-- ========================================
-- 4. AUTORES
-- ========================================
INSERT INTO Autores (nombre)
SELECT DISTINCT autor_nombre
FROM dblink(
    'dbname=biblioteca_legacy user=postgres password=l37jjbc0506',
    'SELECT autor_nombre FROM Biblioteca_Data'
) AS t(autor_nombre TEXT);

-- ========================================
-- 5. LIBRO_AUTOR
-- ========================================
INSERT INTO Libro_Autor (id_libro, id_autor)
SELECT 
    l.id_libro,
    a.id_autor
FROM dblink(
    'dbname=biblioteca_legacy user=postgres password=l37jjbc0506',
    'SELECT titulo_libro, autor_nombre FROM Biblioteca_Data'
) AS b(titulo TEXT, autor TEXT)
JOIN Libros l ON TRIM(b.titulo) = TRIM(l.titulo)
JOIN Autores a ON TRIM(b.autor) = TRIM(a.nombre);

-- ========================================
-- 6. CATEGORIAS (NUEVO)
-- ========================================
INSERT INTO Categorias (nombre, descripcion)
SELECT DISTINCT 
    TRIM(split_part(cat_desc, '/', 1)),
    TRIM(split_part(cat_desc, '/', 2))
FROM dblink(
    'dbname=biblioteca_legacy user=postgres password=l37jjbc0506',
    'SELECT categoria_y_descripcion FROM Biblioteca_Data'
) AS t(cat_desc TEXT);

-- ========================================
-- 7. LIBRO_CATEGORIA (NUEVO)
-- ========================================
INSERT INTO Libro_Categoria (id_libro, id_categoria)
SELECT 
    l.id_libro,
    c.id_categoria
FROM dblink(
    'dbname=biblioteca_legacy user=postgres password=l37jjbc0506',
    'SELECT titulo_libro, categoria_y_descripcion FROM Biblioteca_Data'
) AS b(titulo TEXT, cat_desc TEXT)
JOIN Libros l ON TRIM(b.titulo) = TRIM(l.titulo)
JOIN Categorias c 
ON TRIM(split_part(b.cat_desc, '/', 1)) = TRIM(c.nombre);

-- ========================================
-- 8. USUARIOS
-- ========================================
INSERT INTO Usuarios (nombre, correo)
SELECT DISTINCT nombre_usuario, correo_usuario
FROM dblink(
    'dbname=biblioteca_legacy user=postgres password=l37jjbc0506',
    'SELECT nombre_usuario, correo_usuario FROM Prestamos_Crudos'
) AS t(nombre_usuario TEXT, correo_usuario TEXT);

-- ========================================
-- 9. PRESTAMOS
-- ========================================
INSERT INTO Prestamos (id_usuario, fecha_salida, estado)
SELECT 
    u.id_usuario,
    p.fecha,
    p.estado
FROM dblink(
    'dbname=biblioteca_legacy user=postgres password=l37jjbc0506',
    'SELECT correo_usuario, fecha_salida, estado_prestamo FROM Prestamos_Crudos'
) AS p(correo TEXT, fecha DATE, estado TEXT)
JOIN Usuarios u ON TRIM(p.correo) = TRIM(u.correo);

-- ========================================
-- 10. PRESTAMO_LIBRO (SIMULADO)
-- ========================================
INSERT INTO Prestamo_Libro (id_prestamo, id_libro)
SELECT 
    p.id_prestamo,
    l.id_libro
FROM Prestamos p
JOIN Libros l ON random() < 0.3;

-- ========================================
-- 11. RESEÑAS
-- ========================================
INSERT INTO Reseñas (id_usuario, id_libro, comentario, calificacion)
SELECT 
    u.id_usuario,
    l.id_libro,
    r.comentario,
    r.calificacion::INT
FROM dblink(
    'dbname=biblioteca_legacy user=postgres password=l37jjbc0506',
    'SELECT usuario_id, libro_titulo, comentario, calificacion FROM Reseñas_Usuarios'
) AS r(usuario_id INT, libro TEXT, comentario TEXT, calificacion TEXT)
JOIN Libros l ON TRIM(r.libro) = TRIM(l.titulo)
JOIN Usuarios u ON u.id_usuario = r.usuario_id;

-- ========================================
-- 12. SEDES
-- ========================================
INSERT INTO Sedes (nombre, ubicacion)
SELECT DISTINCT nombre, ubicacion
FROM dblink(
    'dbname=biblioteca_legacy user=postgres password=l37jjbc0506',
    'SELECT sede_nombre, ubicacion_sede FROM Inventario_Sedes'
) AS t(nombre TEXT, ubicacion TEXT);

-- ========================================
-- 13. INVENTARIO
-- ========================================
INSERT INTO Inventario (id_sede, id_libro, cantidad)
SELECT 
    s.id_sede,
    l.id_libro,
    i.cantidad
FROM dblink(
    'dbname=biblioteca_legacy user=postgres password=l37jjbc0506',
    'SELECT sede_nombre, libro_asociado, cantidad_total FROM Inventario_Sedes'
) AS i(sede TEXT, libro TEXT, cantidad INT)
JOIN Sedes s ON TRIM(i.sede) = TRIM(s.nombre)
JOIN Libros l ON TRIM(i.libro) = TRIM(l.titulo);

-- ACTIVAR TRIGGERS
ALTER TABLE Prestamo_Libro ENABLE TRIGGER ALL;