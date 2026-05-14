CREATE OR REPLACE FUNCTION obtener_libros_por_categoria(p_categoria TEXT)
RETURNS TABLE(
    titulo TEXT,
    categoria TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.titulo,
        c.nombre
    FROM Libros l
    JOIN Libro_Categoria lc ON l.id_libro = lc.id_libro
    JOIN Categorias c ON lc.id_categoria = c.id_categoria
    WHERE c.nombre = p_categoria;
END;
$$; SELECT * FROM obtener_libros_por_categoria('Terror');