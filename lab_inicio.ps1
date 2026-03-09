# ============================================================
# lab_inicio.ps1 — Setup automatico en PC laboratorio UCN
# ADSE 2026 — Edificio 1 (20 pisos, muros HA)
#
# USO: Ejecutar con PowerShell como Administrador
#   1. Click derecho en PowerShell → "Run as administrator"
#   2. cd C:\Users\Civil\Desktop
#   3. .\lab_inicio.ps1
# ============================================================

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  TALLER ADSE 2026 — Setup PC Laboratorio" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# --- PASO 1: Matar TODOS los ETABS ---
Write-Host "[1/5] Cerrando ETABS..." -ForegroundColor Yellow
Get-Process ETABS -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process ETABS_ni -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "      OK - procesos terminados" -ForegroundColor Green

# --- PASO 2: Limpiar cache comtypes (evita vtable mismatch v19/v21) ---
Write-Host "[2/5] Limpiando cache comtypes..." -ForegroundColor Yellow
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Path
if ($pythonPath) {
    $sitePackages = & python -c 'import site; print(site.getsitepackages()[0])' 2>$null
    if ($sitePackages) {
        $genPath = Join-Path $sitePackages "comtypes\gen"
        if (Test-Path $genPath) {
            Get-ChildItem $genPath -Exclude "__init__.py","__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "      OK - $genPath limpiado" -ForegroundColor Green
        } else {
            Write-Host "      OK - no habia cache" -ForegroundColor Green
        }
    }
} else {
    Write-Host "      [WARN] Python no encontrado en PATH" -ForegroundColor Red
}

# --- PASO 3: Abrir ETABS 19 ---
Write-Host "[3/5] Abriendo ETABS 19..." -ForegroundColor Yellow
$etabs19 = "C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"
$etabs21 = "C:\Program Files\Computers and Structures\ETABS 21\ETABS.exe"

if (Test-Path $etabs19) {
    Start-Process $etabs19
    Write-Host "      OK - ETABS 19 iniciado" -ForegroundColor Green
    Write-Host "      Esperando 25 segundos a que cargue..." -ForegroundColor Yellow
    for ($i = 25; $i -gt 0; $i--) {
        Write-Host "      $i..." -NoNewline
        Start-Sleep -Seconds 1
    }
    Write-Host ""
} else {
    Write-Host "      [WARN] ETABS 19 no encontrado en ruta estandar" -ForegroundColor Red
    Write-Host "      Abrir ETABS 19 manualmente y presionar ENTER cuando cargue"
    Read-Host
}

# --- PASO 4: Descargar scripts del repo ---
Write-Host "[4/5] Descargando scripts de GitHub..." -ForegroundColor Yellow
$desktop = [Environment]::GetFolderPath("Desktop")
$destDir = Join-Path $desktop "ta"

# Limpiar directorio anterior si existe
if (Test-Path $destDir) {
    Remove-Item $destDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $destDir -Force | Out-Null

$zipUrl = "https://github.com/kcortes765/taller-etabs/archive/refs/heads/master.zip"
$zipPath = Join-Path $desktop "ta.zip"

try {
    Write-Host "      Descargando ZIP..." -ForegroundColor Yellow
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing

    Write-Host "      Extrayendo..." -ForegroundColor Yellow
    Expand-Archive -Path $zipPath -DestinationPath $destDir -Force

    # Mover archivos de la subcarpeta al destino
    $subDir = Join-Path $destDir "taller-etabs-master"
    if (Test-Path $subDir) {
        Get-ChildItem $subDir | Copy-Item -Destination $destDir -Recurse -Force
        Remove-Item $subDir -Recurse -Force
    }
    Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

    Write-Host "      OK - Scripts en: $destDir" -ForegroundColor Green
} catch {
    Write-Host "      [ERROR] Descarga fallida: $_" -ForegroundColor Red
    Write-Host "      Alternativa: Copiar los scripts desde USB a $destDir"
    Write-Host "      Presionar ENTER cuando los scripts esten en $destDir"
    Read-Host
}

# --- PASO 5: Verificar Python y dependencias ---
Write-Host "[5/5] Verificando Python y comtypes..." -ForegroundColor Yellow
Set-Location $destDir

$pyCheck = & python -c "import comtypes; print('comtypes OK')" 2>&1
if ($pyCheck -match "OK") {
    Write-Host "      OK - Python y comtypes disponibles" -ForegroundColor Green
} else {
    Write-Host "      [WARN] comtypes no disponible: $pyCheck" -ForegroundColor Red
    Write-Host "      Instalar: pip install comtypes"
    Read-Host "Presionar ENTER cuando este instalado"
}

# --- LISTO ---
Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  SETUP COMPLETADO" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Directorio: $destDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "  SIGUIENTE PASO — Abrir otra terminal y ejecutar:" -ForegroundColor White
Write-Host ""
Write-Host "  cd $destDir" -ForegroundColor Yellow
Write-Host "  .\EJECUTAR.ps1       <- wrapper completo" -ForegroundColor Yellow
Write-Host "  # o manualmente: python diag.py ; python run_all.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "  IMPORTANTE mientras corre run_all.py:" -ForegroundColor Red
Write-Host "  - NO HACER CLIC en la ventana de ETABS" -ForegroundColor Red
Write-Host "  - Si ETABS dice 'No responde', NO cerrar — esperar" -ForegroundColor Red
Write-Host ""
Write-Host "  Presionar ENTER para abrir la terminal en $destDir" -ForegroundColor White
Read-Host

# Abrir nueva terminal en el directorio de trabajo
Start-Process powershell -ArgumentList "-NoExit", "-NoProfile", "-Command", "Set-Location '$destDir'"
