@echo off
setlocal

:: ============================================================
:: build.bat — Genera CrawlCompare.exe
:: Ejecutar desde cualquier lugar, siempre funciona.
:: ============================================================

set CONDA_ENV=crawler
set SPEC_FILE=%~dp0crawl_compare.spec
set DIST_DIR=%~dp0dist
set BUILD_DIR=%~dp0build
:: Modelo --onedir: el .exe queda dentro de dist\CrawlCompare\ (con _internal\ al lado).
set EXE_PATH=%DIST_DIR%\CrawlCompare\CrawlCompare.exe

echo.
echo =============================================
echo  CrawlCompare — Build de distribución
echo =============================================
echo.

:: Verificar que conda esté disponible
where conda >nul 2>&1
if errorlevel 1 (
    echo [ERROR] conda no encontrado en el PATH.
    echo Abrí este .bat desde Anaconda Prompt.
    pause
    exit /b 1
)

:: Instalar PyInstaller en el env si no está
echo [1/4] Verificando PyInstaller...
call conda run -n %CONDA_ENV% python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo      No encontrado, instalando...
    call conda run -n %CONDA_ENV% pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar PyInstaller.
        pause
        exit /b 1
    )
)
echo      OK

:: Limpiar builds anteriores
echo [2/4] Limpiando builds anteriores...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
echo      OK

:: Ejecutar PyInstaller
echo [3/4] Compilando .exe...
echo.
call conda run -n %CONDA_ENV% pyinstaller "%SPEC_FILE%" --distpath "%DIST_DIR%" --workpath "%BUILD_DIR%"

if errorlevel 1 (
    echo.
    echo [ERROR] El build falló. Revisá los mensajes arriba.
    pause
    exit /b 1
)

:: Smoke test: corre el .exe con --self-test para verificar que todos los
:: módulos críticos cargan bien. Si algo falta en el bundle, falla acá
:: en vez de aparecer como bug en producción.
echo.
echo [4/4] Corriendo smoke test del .exe...
echo.
"%EXE_PATH%" --self-test
if errorlevel 1 (
    echo.
    echo [ERROR] Smoke test FALLO. El .exe tiene problemas de bundling.
    echo         Revisá los [SMOKE] FAIL arriba y agregá lo que falta a
    echo         Deploy\build_manifest.py, luego rebuildea.
    pause
    exit /b 1
)

echo.
echo =============================================
echo  Build exitoso!
echo  Ejecutable: %EXE_PATH%
echo  Smoke test: OK
echo =============================================
echo.
pause
