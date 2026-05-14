CREATE OR REPLACE PROCEDURE generar_log_prestamos()
LANGUAGE plpgsql
AS $$
DECLARE
    registro RECORD;
    cursor_prestamos CURSOR FOR
    SELECT 
        p.id_prestamo,
        u.nombre,
        p.fecha_salida
    FROM Prestamos p
    JOIN Usuarios u ON p.id_usuario = u.id_usuario
    WHERE p.estado = 'Activo';
BEGIN
    OPEN cursor_prestamos;
    LOOP
        FETCH cursor_prestamos INTO registro;
        EXIT WHEN NOT FOUND;
        INSERT INTO Log_Prestamos (id_prestamo, usuario, fecha_salida)
        VALUES (registro.id_prestamo, registro.nombre, registro.fecha_salida);
    END LOOP;
    CLOSE cursor_prestamos;
END;
$$;

-- RUN_QUERY

CALL generar_log_prestamos();