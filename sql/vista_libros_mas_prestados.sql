CREATE OR REPLACE VIEW vista_libros_mas_prestados AS
SELECT *
FROM (
    SELECT 
        l.titulo,
        u.nombre AS usuario,
        COUNT(pl.id_libro) OVER (PARTITION BY l.id_libro) AS veces_prestado
    FROM Prestamo_Libro pl
    JOIN Libros l ON pl.id_libro = l.id_libro
    JOIN Prestamos p ON pl.id_prestamo = p.id_prestamo
    JOIN Usuarios u ON p.id_usuario = u.id_usuario
) sub
ORDER BY veces_prestado DESC;

SELECT * FROM vista_libros_mas_prestados LIMIT 200;