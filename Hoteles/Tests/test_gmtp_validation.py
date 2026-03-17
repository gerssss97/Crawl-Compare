"""Test temporal para verificar validación de GMTP_KEY."""

import os
import sys

# Asegurar que GMTP_KEY no esté configurada
os.environ.pop('GMTP_KEY', None)

from Core.controller import enviar_email_discrepancia

try:
    enviar_email_discrepancia(
        'Test Hotel',
        'Test Room',
        '100',
        '120',
        'test@test.com',
        'dest@test.com'
    )
    print('ERROR: Deberia haber lanzado ValueError')
    sys.exit(1)
except ValueError as e:
    print('SUCCESS: ValueError capturado correctamente')
    print(f'Mensaje de error: {str(e)[:150]}')
    sys.exit(0)
except Exception as e:
    print(f'ERROR: Excepcion inesperada: {type(e).__name__}: {e}')
    sys.exit(1)
