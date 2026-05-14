CREATE OR REPLACE PROCEDURE registrar_prestamo(
    p_correo TEXT,
    p_id_libro INT,
    p_estado TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_usuario INT;
    v_id_prestamo INT;
BEGIN
    -- Obtener usuario
    SELECT id_usuario INTO v_id_usuario
    FROM Usuarios
    WHERE correo = p_correo;

    IF v_id_usuario IS NULL THEN
        RAISE EXCEPTION 'Usuario no encontrado';
    END IF;

    -- Insertar préstamo
    INSERT INTO Prestamos (id_usuario, fecha_salida, estado)
    VALUES (v_id_usuario, CURRENT_DATE, p_estado)
    RETURNING id_prestamo INTO v_id_prestamo;

    -- Relacionar libro
    INSERT INTO Prestamo_Libro (id_prestamo, id_libro)
    VALUES (v_id_prestamo, p_id_libro);

END;
$$; CALL registrar_prestamo('correo@ejemplo.com', 1, 'Activo');