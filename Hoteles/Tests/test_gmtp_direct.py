"""Test directo de validación de GMTP_KEY."""

import os

# Test 1: Variable no existe
print("Test 1: Variable GMTP_KEY no existe")
os.environ.pop('GMTP_KEY', None)
clave = os.getenv("GMTP_KEY")
print(f"  Valor: {repr(clave)}")
print(f"  Validacion 'if not clave': {not clave}")

# Test 2: Variable existe pero está vacía
print("\nTest 2: Variable GMTP_KEY existe pero esta vacia")
os.environ['GMTP_KEY'] = ""
clave = os.getenv("GMTP_KEY")
print(f"  Valor: {repr(clave)}")
print(f"  Validacion 'if not clave': {not clave}")

# Test 3: Variable existe con valor
print("\nTest 3: Variable GMTP_KEY existe con valor")
os.environ['GMTP_KEY'] = "test_value"
clave = os.getenv("GMTP_KEY")
print(f"  Valor: {repr(clave)}")
print(f"  Validacion 'if not clave': {not clave}")

# Test 4: Probar la función directamente
print("\nTest 4: Probar funcion enviar_email_discrepancia sin GMTP_KEY")
os.environ.pop('GMTP_KEY', None)

from Core.controller import enviar_email_discrepancia

try:
    result = enviar_email_discrepancia(
        'Test Hotel',
        'Test Room',
        '100',
        '120',
        'test@test.com',
        'dest@test.com'
    )
    print(f"  ERROR: No lanzo ValueError, retorno: {result}")
except ValueError as e:
    print(f"  SUCCESS: ValueError lanzado con mensaje:")
    print(f"  {str(e)[:100]}")
except Exception as e:
    print(f"  ERROR: Otra excepcion: {type(e).__name__}: {e}")
