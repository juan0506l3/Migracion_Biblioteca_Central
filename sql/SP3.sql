CREATE OR REPLACE PROCEDURE registrar_resena(
    p_id_usuario INT,
    p_id_libro INT,
    p_comentario TEXT,
    p_calificacion INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_calificacion < 1 OR p_calificacion > 5 THEN
        RAISE EXCEPTION 'Calificación inválida (1-5)';
    END IF;

    INSERT INTO Reseñas (id_usuario, id_libro, comentario, calificacion)
    VALUES (p_id_usuario, p_id_libro, p_comentario, p_calificacion);
END;
$$; CALL registrar_resena(1, 2, 'Muy buen libro', 5);