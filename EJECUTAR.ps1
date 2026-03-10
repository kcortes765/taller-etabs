##############################################################
# EJECUTAR.ps1 — Wrapper no interactivo para el pipeline ETABS
# Uso: cd "C:\Users\Civil\Desktop\ta"; .\EJECUTAR.ps1
##############################################################

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  EDIFICIO 1 - 20 PISOS MUROS - TALLER ADSE 2026" -ForegroundColor Cyan
Write-Host "  Flujo no interactivo: diagnostico -> pipeline estable -> resultados" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "`n--- Paso 1: Diagnostico de conexion ---" -ForegroundColor Yellow
python diag.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "diag.py fallo. Revisar COM/ETABS antes de seguir." -ForegroundColor Red
    exit 1
}

Write-Host "`n--- Paso 2: Pipeline estable (reinicia ETABS entre fases) ---" -ForegroundColor Yellow
python run_all.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "run_all.py fallo. Revisar el log arriba." -ForegroundColor Red
    exit 1
}

Write-Host "`n--- Paso 3: Resumen final ---" -ForegroundColor Yellow
python 12_results.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  EJECUCION COMPLETADA" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
