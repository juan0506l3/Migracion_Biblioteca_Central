CREATE TABLE IF NOT EXISTS Log_Prestamos (
    id_log SERIAL PRIMARY KEY,
    id_prestamo INT,
    usuario TEXT,
    fecha_salida DATE,
    fecha_log TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);