CREATE OR REPLACE PROCEDURE devolver_libro(
    p_id_prestamo INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE Prestamos
    SET estado = 'Devuelto'
    WHERE id_prestamo = p_id_prestamo;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Préstamo no existe';
    END IF;
END;
$$; CALL devolver_libro(1);