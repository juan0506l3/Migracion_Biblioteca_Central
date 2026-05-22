"""
tests/test_pipeline.py
Pruebas unitarias para el pipeline de calidad de datos.
Compatible con pytest y unittest estándar de Python.

Ejecutar con pytest:
    pytest tests/ -v --cov=main --cov-report=term-missing

Ejecutar con unittest (sin instalar nada):
    python3 -m unittest discover tests/ -v
"""

import sys
import os
import unittest
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    limpiar_texto,
    normalizar_fecha,
    parse_cantidad,
    normalizar_calificacion,
    hash_correo,
    es_correo_valido,
)


# ─────────────────────────────────────────────
# Tests: limpiar_texto
# ─────────────────────────────────────────────
class TestLimpiarTexto(unittest.TestCase):
    def test_elimina_espacios_extra(self):
        self.assertEqual(limpiar_texto("  hola   mundo  "), "Hola Mundo")

    def test_elimina_tabulaciones(self):
        self.assertEqual(limpiar_texto("pedro\tparamo"), "Pedro Paramo")

    def test_titulo_case(self):
        self.assertEqual(limpiar_texto("GABRIEL GARCIA MARQUEZ"), "Gabriel Garcia Marquez")

    def test_nan_devuelve_nan(self):
        resultado = limpiar_texto(float("nan"))
        self.assertTrue(resultado is None or (isinstance(resultado, float) and math.isnan(resultado)))

    def test_none_devuelve_none(self):
        self.assertIsNone(limpiar_texto(None))

    def test_cadena_vacia(self):
        self.assertEqual(limpiar_texto("   "), "")

    def test_texto_normal(self):
        self.assertEqual(limpiar_texto("Rayuela"), "Rayuela")


# ─────────────────────────────────────────────
# Tests: normalizar_fecha
# ─────────────────────────────────────────────
class TestNormalizarFecha(unittest.TestCase):
    def test_formato_dd_mm_yyyy(self):
        self.assertEqual(normalizar_fecha("27/12/1986"), "1986-12-27")

    def test_formato_yyyy_mm_dd(self):
        self.assertEqual(normalizar_fecha("2024-02-11"), "2024-02-11")

    def test_sin_fecha_devuelve_none(self):
        self.assertIsNone(normalizar_fecha("Sin fecha"))

    def test_desconocida_devuelve_none(self):
        self.assertIsNone(normalizar_fecha("Desconocida"))

    def test_na_devuelve_none(self):
        self.assertIsNone(normalizar_fecha("N/A"))

    def test_nan_devuelve_none(self):
        self.assertIsNone(normalizar_fecha(float("nan")))

    def test_cadena_vacia_devuelve_none(self):
        self.assertIsNone(normalizar_fecha(""))

    def test_solo_año(self):
        self.assertEqual(normalizar_fecha("1954"), "1954-01-01")


# ─────────────────────────────────────────────
# Tests: parse_cantidad
# ─────────────────────────────────────────────
class TestParseCantidad(unittest.TestCase):
    def test_numero_entero(self):
        self.assertEqual(parse_cantidad(43), 43)

    def test_numero_como_string(self):
        self.assertEqual(parse_cantidad("43"), 43)

    def test_palabra_diez(self):
        self.assertEqual(parse_cantidad("Diez"), 10)

    def test_palabra_uno(self):
        self.assertEqual(parse_cantidad("uno"), 1)

    def test_negativo_devuelve_none(self):
        self.assertIsNone(parse_cantidad(-5))

    def test_nan_devuelve_none(self):
        self.assertIsNone(parse_cantidad(float("nan")))

    def test_texto_invalido_devuelve_none(self):
        self.assertIsNone(parse_cantidad("mucho"))

    def test_float_convierte_a_int(self):
        self.assertEqual(parse_cantidad(7.9), 7)

    def test_cero_es_valido(self):
        self.assertEqual(parse_cantidad(0), 0)


# ─────────────────────────────────────────────
# Tests: normalizar_calificacion
# ─────────────────────────────────────────────
class TestNormalizarCalificacion(unittest.TestCase):
    def test_numero_directo(self):
        self.assertEqual(normalizar_calificacion("3"), 3)

    def test_formato_sobre_5(self):
        self.assertEqual(normalizar_calificacion("5/5"), 5)

    def test_formato_4_sobre_5(self):
        self.assertEqual(normalizar_calificacion("4/5"), 4)

    def test_palabra_cinco(self):
        self.assertEqual(normalizar_calificacion("Cinco"), 5)

    def test_palabra_dos(self):
        self.assertEqual(normalizar_calificacion("dos"), 2)

    def test_rango_invalido(self):
        self.assertIsNone(normalizar_calificacion("2-5"))

    def test_fuera_de_rango_alto(self):
        self.assertIsNone(normalizar_calificacion("10"))

    def test_fuera_de_rango_bajo(self):
        self.assertIsNone(normalizar_calificacion("0"))

    def test_nan_devuelve_none(self):
        self.assertIsNone(normalizar_calificacion(float("nan")))

    def test_entero_directo(self):
        self.assertEqual(normalizar_calificacion(4), 4)


# ─────────────────────────────────────────────
# Tests: hash_correo
# ─────────────────────────────────────────────
class TestHashCorreo(unittest.TestCase):
    def test_produce_sha256(self):
        resultado = hash_correo("test@correo.com")
        self.assertIsInstance(resultado, str)
        self.assertEqual(len(resultado), 64)

    def test_mismo_input_mismo_hash(self):
        self.assertEqual(hash_correo("a@b.com"), hash_correo("a@b.com"))

    def test_diferente_input_diferente_hash(self):
        self.assertNotEqual(hash_correo("a@b.com"), hash_correo("c@d.com"))

    def test_none_devuelve_none(self):
        self.assertIsNone(hash_correo(None))

    def test_nan_devuelve_none(self):
        self.assertIsNone(hash_correo(float("nan")))

    def test_hash_no_contiene_correo(self):
        correo = "secreto@empresa.com"
        resultado = hash_correo(correo)
        self.assertNotIn(correo, resultado)


# ─────────────────────────────────────────────
# Tests: es_correo_valido
# ─────────────────────────────────────────────
class TestEsCorreoValido(unittest.TestCase):
    def test_correo_valido(self):
        self.assertTrue(es_correo_valido("m.garcia@email.com"))

    def test_correo_con_subdominio(self):
        self.assertTrue(es_correo_valido("user@mail.empresa.co"))

    def test_correo_invalido_at_escrito(self):
        self.assertFalse(es_correo_valido("usuario_at_email.com"))

    def test_correo_sin_dominio(self):
        self.assertFalse(es_correo_valido("usuario@"))

    def test_correo_sin_arroba(self):
        self.assertFalse(es_correo_valido("usuarioemail.com"))

    def test_correo_vacio(self):
        self.assertFalse(es_correo_valido(""))

    def test_correo_con_caracteres_validos(self):
        self.assertTrue(es_correo_valido("user+test@domain.org"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
