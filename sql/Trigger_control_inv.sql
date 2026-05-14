CREATE OR REPLACE FUNCTION fn_controlar_inventario()
RETURNS TRIGGER AS $$
DECLARE
    v_stock INT;
BEGIN
    SELECT cantidad INTO v_stock
    FROM Inventario
    WHERE id_libro = NEW.id_libro
    LIMIT 1;

    IF v_stock IS NULL THEN
        RAISE EXCEPTION 'El libro no existe en inventario';
    END IF;

    IF v_stock <= 0 THEN
        RAISE EXCEPTION 'No hay stock disponible';
    END IF;

    UPDATE Inventario
    SET cantidad = cantidad - 1
    WHERE id_libro = NEW.id_libro;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
----
CREATE TRIGGER trg_controlar_inventario
BEFORE INSERT ON Prestamo_Libro
FOR EACH ROW
EXECUTE FUNCTION fn_controlar_inventario();
----
INSERT INTO Prestamo_Libro (id_prestamo, id_libro)
VALUES (1, 1);