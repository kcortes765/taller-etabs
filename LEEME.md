# Taller ETABS — Edificio 1 (20 pisos, muros)
# Pipeline completo: geometria → analisis → resultados

## Descargar (PC lab sin git)

```powershell
cd C:\Users\Civil\Desktop
Invoke-WebRequest -Uri "https://github.com/kcortes765/taller-etabs/archive/refs/heads/master.zip" -OutFile ta.zip
Expand-Archive ta.zip -DestinationPath ta -Force
Copy-Item ta\taller-etabs-master\* ta\ -Force -Recurse
Remove-Item ta\taller-etabs-master, ta.zip -Recurse -Force
cd ta
```

## Requisitos
- Python 3.12 (ya instalado en lab)
- `pip install comtypes`
- ETABS 19 o 21

## Ejecutar

```powershell
# 1. MATAR TODO ETABS
Get-Process ETABS -EA SilentlyContinue | Stop-Process -Force
Start-Sleep 3

# 2. ABRIR ETABS 19
Start-Process "C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"
Start-Sleep 20

# 3. DIAGNOSTICO (primera vez en PC nuevo):
cd C:\Users\Civil\Desktop\ta
python diag.py

# 4. EJECUTAR TODO:
python run_all.py
```

## Pipeline (13 pasos)

| Paso | Script | Que hace |
|------|--------|----------|
| 1 | 01_init_model.py | 20 pisos (3.4m + 19x2.6m = 52.8m) |
| 2 | 02_materials_sections.py | G30, A630-420H, secciones |
| 3 | 03_walls.py | ~960 muros (30cm y 20cm) |
| 4 | 04_beams.py | ~400 vigas VI20/60 |
| 5 | 05_slabs.py | ~700 losas 15cm |
| 6 | 06_loads.py | PP, SCP, SCT, TERP, TERT, SEx, SEy |
| 7 | 07_diaphragm_supports.py | Diafragma rigido + empotramientos base |
| 8 | 08_spectrum_cases.py | Espectro NCh433, modal 60 modos, RS SEx/SEy, combos NCh3171 |
| 9 | 09_torsion_cases.py | Torsion accidental: caso a (ecc 5%) + caso b forma 2 |
| 10 | 10_save_run.py | Guardar .EDB + Run Analysis |
| 11 | 11_adjust_Rstar.py | Leer T*, calcular R* DS61, re-escalar RS, re-analizar |
| 12 | 12_results.py | Resumen: periodos, corte basal, drift, peso sismico |
| 13 | 13_semirigid.py | SaveAs sin diafragma rigido → Edificio1_SemiRigido.edb |

## Los 6 casos de analisis del enunciado

| Caso | Diafragma | Torsion | Implementacion |
|------|-----------|---------|----------------|
| 1 | Rigido | Caso a) | SEx/SEy con ecc override 5% |
| 2 | Rigido | Caso b) Forma 1 | **MANUAL** (ver abajo) |
| 3 | Rigido | Caso b) Forma 2 | SEx_b2/SEy_b2 + TorX/TorY |
| 4 | Semi-rigido | Caso a) | Edificio1_SemiRigido.edb |
| 5 | Semi-rigido | Caso b) Forma 1 | **MANUAL** |
| 6 | Semi-rigido | Caso b) Forma 2 | Semi-rigido + combos b2 |

## Caso b) Forma 1 — Instrucciones manuales

La Forma 1 requiere desplazar fisicamente el centro de masa ±5% de la
dimension perpendicular. En ETABS:

1. Abrir el modelo (Edificio1.edb)
2. Define > Diaphragm Eccentricity Overrides
3. Para cada piso, shift el CM:
   - Sismo X: ΔCM_y = ±0.05 × 13.821m = ±0.691m
   - Sismo Y: ΔCM_x = ±0.05 × 38.505m = ±1.925m
4. Crear RS cases separados para cada combinacion de signo
5. Correr analisis

## Archivos generados

| Archivo | Contenido |
|---------|-----------|
| Edificio1.edb | Modelo con diafragma rigido, espectro con R* |
| Edificio1_SemiRigido.edb | Modelo sin diafragma rigido |
| espectro_nch433.txt | Espectro para importar manual (T vs Sa/g) |

## Si algo falla

### Espectro no se define via API
Importar manualmente:
1. Define > Functions > Response Spectrum > User Defined
2. Nombre: `Espectro_NCh433`
3. Importar desde `espectro_nch433.txt` (columna 1: T, columna 2: Sa/g)

### Mass source no se define via API
1. Define > Mass Source
2. Include Element Self Mass: SI
3. Agregar: TERP factor 1.0, SCP factor 0.25

### 0 empotramientos
El script imprime [DEBUG] con el formato de GetCoordCartesian.
Si los puntos no se empotran:
1. Select > By Properties > Points at z=0
2. Assign > Joint > Restraints > Fixed

### Conexion falla
1. `python diag.py` — ver que metodos funcionan
2. Matar TODOS los ETABS, abrir solo v19, esperar 20s
3. Si nada funciona: `"...\ETABS.exe" /regserver` como admin

## Parametros sismicos (Antofagasta Zona 3, Suelo C)

| Parametro | Valor |
|-----------|-------|
| Ao/g | 0.40 |
| S | 1.05 |
| To | 0.40 s |
| T' | 0.45 s |
| n | 1.40 |
| p | 1.60 |
| Ro | 11 (muros HA) |
| I | 1.0 (oficinas) |
| ξ | 5% |

## Despues del pipeline

1. Verificar vista 3D en ETABS
2. Verificar peso sismico (~1 tonf/m2/piso)
3. Verificar drift < 0.002 en CM
4. Si mass source o espectro fallaron → definir manualmente
5. Diseño de muros: Section Designer en ETABS o SAP2000 para curvas M-φ
