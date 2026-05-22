-- schema_sucio.sql
-- Script SQL con datos sucios para el ejercicio de limpieza
-- Taller Final - Calidad de Software - Unisabaneta

-- ─────────────────────────────────────────────────────────
-- 1. Tabla principal (viola 1FN: categoria_y_descripcion
--    contiene múltiples valores; fecha_publicacion en
--    formatos mixtos; IDs y filas duplicadas)
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Biblioteca_Data" (
    id_registro           INTEGER,
    titulo_libro          TEXT,
    autor_nombre          TEXT,
    categoria_y_descripcion TEXT,
    editorial_info        TEXT,
    fecha_publicacion     TEXT
);

-- ─────────────────────────────────────────────────────────
-- 2. Tabla de préstamos (viola 1FN: libros_prestados
--    contiene varios libros separados por coma;
--    correos con formato inválido)
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Prestamos_Crudos" (
    id_prestamo      INTEGER,
    nombre_usuario   TEXT,
    correo_usuario   TEXT,
    libros_prestados TEXT,
    fecha_salida     TEXT,
    estado_prestamo  TEXT
);

-- ─────────────────────────────────────────────────────────
-- 3. Inventario por sede (cantidad_total con texto y
--    valores negativos)
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Inventario_Sedes" (
    sede_nombre    TEXT,
    ubicacion_sede TEXT,
    libro_asociado TEXT,
    cantidad_total TEXT
);

-- ─────────────────────────────────────────────────────────
-- 4. Reseñas (calificación en formatos variados,
--    usuario_id con texto no válido)
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "Reseñas_Usuarios" (
    usuario_id   TEXT,
    libro_titulo TEXT,
    comentario   TEXT,
    calificacion TEXT
);

-- ─────────────────────────────────────────────────────────
-- Datos de ejemplo con anomalías inyectadas
-- ─────────────────────────────────────────────────────────
INSERT INTO "Biblioteca_Data" VALUES
(322, 'El Aleph - Ed 322',   'Mario Vargas Llosa', 'Historia; Biografía',   'Alfaguara (Madrid)',          '9/3/1954'),
(883, 'El Aleph - Ed 883',   'Mario Benedetti',    'Poesía; Antología',     'Planeta (Barcelona)',         NULL),
(184, 'Crónica de una muerte anunciada - Ed 184', 'Isabel Allende', 'Poesía; Antología', 'Alfaguara (Madrid)', NULL),
(624, 'La casa de los espíritus - Ed 624', 'mario benedetti', 'Poesía; Antología	', 'Sudamericana (Buenos Aires)', '27/12/1986'),
(172, 'Rayuela - Ed 172',    'Jorge Luis Borges',  'Poesía; Antología',     'Sudamericana (Buenos Aires)', NULL),
-- Fila duplicada intencional
(322, 'El Aleph - Ed 322',   'Mario Vargas Llosa', 'Historia; Biografía',   'Alfaguara (Madrid)',          '9/3/1954');

INSERT INTO "Prestamos_Crudos" VALUES
(1, 'María García',  'm.garcia@email.com',         'Don Quijote de la Mancha - Ed 896, Ficciones - Ed 991', 'Sin fecha',  'Pendiente'),
(2, 'María García',  'm.garcia@email.com',         'El Aleph - Ed 136, El Aleph - Ed 772',                  'Sin fecha',  'Atrasado'),
(3, 'María García',  'm.garcia@email.com',         'Ficciones - Ed 633',                                    '2024-02-11', 'Atrasado'),
(4, 'Ana Martínez',  'ana.mar_libros_at_email.com','Pedro Páramo - Ed 774, Ficciones - Ed 359',             'Sin fecha',  'Atrasado'),
(5, 'MARÍA GARCÍA',  'm.garcia@email.com',         'La ciudad y los perros - Ed 127',                       '2024-03-12', 'Pendiente'),
-- Fila duplicada intencional
(3, 'María García',  'm.garcia@email.com',         'Ficciones - Ed 633',                                    '2024-02-11', 'Atrasado');

INSERT INTO "Inventario_Sedes" VALUES
('Sede Norte',   'Avenida Poblado 12-05', 'Pedro Páramo - Ed 639',              NULL),
('Sede Norte',   'Avenida Poblado 12-05', 'Ficciones - Ed 757',                 'Diez'),
('Sede Central', 'CALLE 10 #45-20',       'Don Quijote de la Mancha - Ed 951',  '43'),
('Sede Norte',   'Avenida Poblado 12-05', 'Ficciones - Ed 524',                 NULL),
('Sede Sur',     'Carrera 5 #23-10',      'Rayuela - Ed 210',                   '-3');

INSERT INTO "Reseñas_Usuarios" VALUES
('Usuario_Desconocido', 'Pedro Páramo - Ed 552',          'Malo',  'Cinco'),
('530',                 'Rayuela - Ed 401',               NULL,    '2-5'),
('Usuario_Desconocido', 'El Aleph - Ed 180',             'MALO',  '4/5'),
('Usuario_Desconocido', 'La ciudad y los perros - Ed 640','BUENO', '3'),
('130',                 'Ficciones - Ed 970	',           'MALO',  '5/5');
