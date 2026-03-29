# Setup del Proyecto

Guía paso a paso para configurar el entorno de desarrollo del comparador de hoteles.

## Requisitos Previos

- Python 3.12+ (el proyecto usa features de Python 3.12)
- Conda o Miniconda instalado
- Git (para clonar el repo)
- Cuenta en Groq Cloud (para API key gratuita de DeepSeek-R1)

---

## 1. Clonar el Repositorio

```bash
git clone <url-del-repo>
cd Hoteles
```

---

## 2. Crear Entorno Virtual con Conda

```bash
# Crear entorno con Python 3.12
conda create -n deep-seek-crawler python=3.12 -y

# Activar entorno
conda activate deep-seek-crawler
```

**Verificar versión de Python:**
```bash
python --version
# Output esperado: Python 3.12.x
```

---

## 3. Instalar Dependencias

```bash
# Instalar todas las dependencias desde requirements.txt
pip install -r requirements.txt
```

### Dependencias Principales

El archivo `requirements.txt` incluye:

```txt
# Web scraping
crawl4ai==0.4.247

# LLM API
groq==0.13.0

# Modelos de datos
pydantic==2.10.6

# Excel parsing
openpyxl>=3.1.0

# UI (CustomTkinter)
# Docs: https://customtkinter.tomschimansky.com
customtkinter>=5.2.0

# Fuzzy matching
rapidfuzz>=3.13.0

# Variables de entorno
python-dotenv==1.0.1

# Testing (opcional)
pytest>=8.0.0
```

**Tiempo de instalación**: ~2-3 minutos (depende de conexión)

---

## 4. Configurar Variables de Entorno

Crear archivo `.env` en el directorio `Hoteles/`:

```bash
# Crear .env desde la raíz del proyecto
touch Hoteles/.env
```

**Contenido del archivo `.env`:**

```env
# ============================================
# API Keys
# ============================================

# Groq API Key (REQUERIDO para scraping)
# Obtener en: https://console.groq.com/keys
GROQ_API_KEY=gsk_tu_api_key_aqui

# Gmail SMTP (OPCIONAL - solo para envío de emails)
# Usar "Contraseña de aplicación" de Google
# Guía: https://support.google.com/accounts/answer/185833
GMTP_KEY=tu_contraseña_de_aplicacion_aqui

# ============================================
# Configuración del Scraper
# ============================================

# Delay entre scraping de periodos (en segundos)
# Default: 2s (evita rate limiting)
SCRAPING_DELAY_SECONDS=2

# ============================================
# Email Config (OPCIONAL)
# ============================================

# Email desde el cual se envían notificaciones
SMTP_USER=tu_email@gmail.com

# Email destinatario de notificaciones
EMAIL_TO=destinatario@example.com
```

### Obtener Groq API Key (Gratis)

1. Ir a [https://console.groq.com](https://console.groq.com)
2. Crear cuenta (gratis, sin tarjeta de crédito)
3. Navegar a "API Keys"
4. Crear nueva key
5. Copiar y pegar en `.env`

**Límites gratuitos**: 14,400 requests/día (más que suficiente para testing)

### Obtener Gmail App Password (Opcional)

Solo necesario si querés enviar emails automáticos:

1. Ir a [https://myaccount.google.com/security](https://myaccount.google.com/security)
2. Activar "Verificación en 2 pasos"
3. Ir a "Contraseñas de aplicación"
4. Crear password para "Mail" > "Windows Computer"
5. Copiar el password de 16 caracteres en `.env`

---

## 5. Verificar Instalación

### Test 1: Imports Básicos

```bash
python -c "
import crawl4ai
import groq
import pydantic
import openpyxl
import rapidfuzz
from dotenv import load_dotenv
print('✅ Todos los imports funcionan correctamente')
"
```

**Output esperado:**
```
✅ Todos los imports funcionan correctamente
```

### Test 2: Cargar Variables de Entorno

```bash
python -c "
from dotenv import load_dotenv
import os

load_dotenv('Hoteles/.env')
api_key = os.getenv('GROQ_API_KEY')

if api_key and api_key.startswith('gsk_'):
    print('✅ GROQ_API_KEY cargada correctamente')
else:
    print('❌ GROQ_API_KEY no configurada o inválida')
"
```

**Output esperado:**
```
✅ GROQ_API_KEY cargada correctamente
```

### Test 3: Ejecutar Extractor de Excel

```bash
cd Hoteles
python Tests/testExtractor2.py
```

**Output esperado:**
```
=== HOTELES ENCONTRADOS ===
Hotel: Alvear Palace
  Tipos: 2
  Habitaciones directas: 0
  Periodos: 3 grupos

... (más detalles)

✅ Extracción completada
```

### Test 4: Test del Scraper (Opcional)

Si tenés la API key configurada:

```bash
cd Hoteles
python -c "
import asyncio
from ScrawlingChinese.crawler import crawl_alvear

async def test():
    hotel = await crawl_alvear(
        fecha_entrada='2026-02-15',
        fecha_salida='2026-02-16',
        adultos=2,
        ninos=0
    )
    print(f'✅ Scraping exitoso: {len(hotel.habitaciones)} habitaciones encontradas')

asyncio.run(test())
"
```

**Output esperado:**
```
✅ Scraping exitoso: 15 habitaciones encontradas
```

**Tiempo**: ~5-10 segundos

---

## 6. Ejecutar la Aplicación

### Opción 1: Interfaz Gráfica (Recomendado)

```bash
cd Hoteles
python app.py
```

Esto abre la ventana Tkinter con la interfaz completa.

### Opción 2: Script de Test

```bash
cd Hoteles
python main.py
```

Ejecuta el extractor de Excel y muestra los datos en consola.

---

## 7. Estructura de Directorios

Después del setup, deberías tener:

```
Hoteles/
├── .env                        ← Variables de entorno (NO hacer commit)
├── app.py                      ← Punto de entrada principal
├── main.py                     ← Script de testing
├── requirements.txt            ← Dependencias
├── Data/
│   └── Extracto_prueba2.xlsx  ← Excel con datos de hoteles
├── Core/                       ← Lógica de negocio
├── Models/                     ← Modelos Pydantic
├── UI/                         ← Interfaz Tkinter
├── ScrawlingChinese/           ← Web scraper
├── ExtractorDatos/             ← Parser de Excel
└── Tests/                      ← Scripts de testing
```

---

## Troubleshooting

### Error: "No module named 'crawl4ai'"

```bash
# Verificar que el entorno esté activado
conda activate deep-seek-crawler

# Re-instalar dependencias
pip install -r requirements.txt
```

### Error: "GROQ_API_KEY not found"

- Verificar que el archivo `.env` exista en `Hoteles/`
- Verificar que la variable esté correctamente escrita (sin espacios)
- Verificar que el script esté cargando `.env` con `load_dotenv('Hoteles/.env')`

### Error: "No such file: Data/Extracto_prueba2.xlsx"

- Verificar que el archivo Excel exista en `Hoteles/Data/`
- Si usás otro nombre de archivo, actualizar en `ExtractorDatos/extractor.py:15`

### Scraper muy lento o timeout

- Aumentar `SCRAPING_DELAY_SECONDS` en `.env`
- Verificar conexión a internet
- Verificar que la API key de Groq sea válida

### Error: "ModuleNotFoundError: No module named 'tkinter'"

En Linux/macOS, instalar tkinter:

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS
brew install python-tk
```

En Windows, tkinter viene incluido con Python.

---

## Próximos Pasos

Una vez que el setup esté completo:

1. 📖 Leer [../arquitectura/overview.md](../arquitectura/overview.md) para entender la estructura
2. 🧪 Ejecutar tests con [testing.md](testing.md)
3. 🐛 Configurar debugging con [debugging.md](debugging.md)
4. 🔍 Explorar el código siguiendo las [convenciones.md](convenciones.md)

---

## Activación Rápida (Daily Use)

Agregá este alias a tu `.bashrc` o `.zshrc`:

```bash
alias hoteles='cd /path/to/Hoteles && conda activate deep-seek-crawler && python app.py'
```

Luego simplemente ejecutá:
```bash
hoteles
```

---

¿Problemas? Consultá [troubleshooting en scraper](../scraper/troubleshooting.md) o [debugging.md](debugging.md).
