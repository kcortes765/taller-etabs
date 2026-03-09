# lab_inicio.ps1 - Setup PC laboratorio UCN ADSE 2026
# USO: powershell -ExecutionPolicy Bypass -File lab_inicio.ps1

Write-Host "======================================================"
Write-Host "  TALLER ADSE 2026 - Setup PC Laboratorio"
Write-Host "======================================================"

# 1. Matar ETABS
Write-Host "[1/5] Cerrando ETABS..."
Get-Process ETABS -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process ETABS_ni -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "      OK"

# 2. Limpiar cache comtypes
Write-Host "[2/5] Limpiando cache comtypes..."
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Path
if ($pythonPath) {
    $sitePackages = & python -c 'import site; print(site.getsitepackages()[0])' 2>$null
    if ($sitePackages) {
        $genPath = Join-Path $sitePackages "comtypes\gen"
        if (Test-Path $genPath) {
            Get-ChildItem $genPath -Exclude "__init__.py","__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "      OK - cache limpiado"
        } else {
            Write-Host "      OK - no habia cache"
        }
    }
} else {
    Write-Host "      WARN: Python no encontrado"
}

# 3. Abrir ETABS 19
Write-Host "[3/5] Abriendo ETABS 19..."
$etabs19 = "C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"
if (Test-Path $etabs19) {
    Start-Process $etabs19
    Write-Host "      Esperando 25 segundos..."
    for ($i = 25; $i -gt 0; $i--) {
        Write-Host "      $i..." -NoNewline
        Start-Sleep -Seconds 1
    }
    Write-Host ""
    Write-Host "      OK - ETABS 19 iniciado"
} else {
    Write-Host "      WARN: ETABS 19 no encontrado"
    Write-Host "      Abrir ETABS 19 manualmente y presionar ENTER"
    Read-Host
}

# 4. Descargar scripts
Write-Host "[4/5] Descargando scripts de GitHub..."
$desktop = [Environment]::GetFolderPath("Desktop")
$destDir = Join-Path $desktop "ta"

if (Test-Path $destDir) {
    Remove-Item $destDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $destDir -Force | Out-Null

$zipUrl = "https://github.com/kcortes765/taller-etabs/archive/refs/heads/master.zip"
$zipPath = Join-Path $desktop "ta.zip"

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
    Expand-Archive -Path $zipPath -DestinationPath $destDir -Force
    $subDir = Join-Path $destDir "taller-etabs-master"
    if (Test-Path $subDir) {
        Get-ChildItem $subDir | Copy-Item -Destination $destDir -Recurse -Force
        Remove-Item $subDir -Recurse -Force
    }
    Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
    Write-Host "      OK - Scripts en: $destDir"
} catch {
    Write-Host "      ERROR: $_"
    Write-Host "      Copiar scripts desde USB a $destDir"
    Read-Host "Presionar ENTER cuando esten listos"
}

# 5. Verificar Python
Write-Host "[5/5] Verificando Python y comtypes..."
Set-Location $destDir
$pyCheck = & python -c 'import comtypes; print("OK")' 2>&1
if ($pyCheck -match "OK") {
    Write-Host "      OK - comtypes disponible"
} else {
    Write-Host "      WARN: $pyCheck"
    Write-Host "      Instalar: pip install comtypes"
    Read-Host "Presionar ENTER cuando este instalado"
}

Write-Host ""
Write-Host "======================================================"
Write-Host "  SETUP COMPLETADO"
Write-Host "======================================================"
Write-Host ""
Write-Host "  Carpeta: $destDir"
Write-Host ""
Write-Host "  SIGUIENTE:"
Write-Host "    cd $destDir"
Write-Host "    python diag.py"
Write-Host "    python run_all.py"
Write-Host ""
