##############################################################
#  EJECUTAR.ps1 — Edificio 1, 20 pisos muros, ADSE 2026
#  Uso:  cd "C:\Users\Civil\Desktop\ta"
#        .\EJECUTAR.ps1
##############################################################

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  EDIFICIO 1 - 20 PISOS MUROS - TALLER ADSE 2026" -ForegroundColor Cyan
Write-Host "  Asegurate de tener ETABS abierto con modelo nuevo vacio" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "Presiona ENTER cuando ETABS este listo"

# --- Paso 0: Test API ---
Write-Host "`n--- Paso 0: Test de conexion API ---" -ForegroundColor Yellow
python 00_test_api.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "El test fallo. Revisa arriba." -ForegroundColor Red
    Read-Host "Presiona ENTER para salir"
    exit 1
}

Write-Host ""
$resp = Read-Host "Test OK? Continuar con el modelo completo? (s/n)"
if ($resp -ne 's') {
    Write-Host "Abortado." -ForegroundColor Red
    exit 0
}

# --- Ejecutar paso a paso ---
$scripts = @(
    @("01_init_model.py",         "Paso 1: Inicializar modelo + 20 pisos"),
    @("02_materials_sections.py", "Paso 2: Materiales y secciones"),
    @("03_walls.py",              "Paso 3: Dibujar muros"),
    @("04_beams.py",              "Paso 4: Dibujar vigas"),
    @("05_slabs.py",              "Paso 5: Dibujar losas"),
    @("06_loads.py",              "Paso 6: Patrones y cargas"),
    @("07_diaphragm_supports.py", "Paso 7: Diafragma + empotramientos"),
    @("08_spectrum_cases.py",     "Paso 8: Espectro, modal, RS, combos")
)

foreach ($step in $scripts) {
    $file = $step[0]
    $desc = $step[1]
    Write-Host "`n============================================================" -ForegroundColor Green
    Write-Host "  $desc" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green

    python $file

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [ERROR] $file fallo" -ForegroundColor Red
        $cont = Read-Host "  Continuar de todos modos? (s/n)"
        if ($cont -ne 's') {
            Write-Host "Abortado." -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  COMPLETADO!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  SIGUIENTE:" -ForegroundColor Yellow
Write-Host "  1. Verificar modelo en vista 3D"
Write-Host "  2. Verificar peso sismico (~1 tonf/m2)"
Write-Host "  3. Run Analysis"
Write-Host "  4. Ajustar R* segun T*"
Write-Host ""
Read-Host "Presiona ENTER para cerrar"
