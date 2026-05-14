CREATE OR REPLACE FUNCTION calcular_multa(p_id_prestamo INT)
RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
    v_fecha_salida DATE;
    v_dias_retraso INT;
    v_multa INT := 0;
BEGIN
    SELECT fecha_salida INTO v_fecha_salida
    FROM Prestamos
    WHERE id_prestamo = p_id_prestamo;

    IF v_fecha_salida IS NULL THEN
        RAISE EXCEPTION 'Préstamo no existe';
    END IF;

    v_dias_retraso := CURRENT_DATE - v_fecha_salida - 7;

    IF v_dias_retraso > 0 THEN
        v_multa := v_dias_retraso * 1000;
    END IF;

    RETURN v_multa;
END;
$$;

-- RUN_QUERY

SELECT
    u.nombre AS usuario,
    u.correo,
    p.id_prestamo,
    p.fecha_salida,
    (CURRENT_DATE - p.fecha_salida - 7) AS dias_retraso,
    calcular_multa(p.id_prestamo)       AS multa_total
FROM Prestamos p
JOIN Usuarios u ON p.id_usuario = u.id_usuario
WHERE p.estado = 'Activo'
  AND (CURRENT_DATE - p.fecha_salida - 7) > 0
ORDER BY multa_total DESC
LIMIT 10;