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

## Pipeline (13 pasos en 4 fases)

### Fase 1: Geometria (critica)
| Paso | Script | Que hace |
|------|--------|----------|
| 1 | 01_init_model.py | 20 pisos + guarda .edb inmediatamente |
| 2 | 02_materials_sections.py | G30, A630-420H, secciones |
| 3 | 03_walls.py | ~960 muros (con verificacion post-creacion) |
| 4 | 04_beams.py | ~400 vigas (con verificacion) |
| 5 | 05_slabs.py | ~700 losas (con verificacion) |
| 6 | 06_loads.py | PP, SCP, SCT, TERP, TERT, SEx, SEy |
| 7 | 07_diaphragm_supports.py | Diafragma rigido + empotramientos base |
| 7b | 07b_save_checkpoint.py | **VERIFICACION COMPLETA** + checkpoint |

### Fase 2: Analisis
| Paso | Script | Que hace |
|------|--------|----------|
| 8 | 08_spectrum_cases.py | Espectro NCh433, modal, mass source, combos |
| 9 | 09_torsion_cases.py | Torsion caso a (ecc 5%) + caso b forma 2 |
| 10 | 10_save_run.py | Guardar .EDB + Run Analysis |

### Fase 3: Post-proceso
| Paso | Script | Que hace |
|------|--------|----------|
| 11 | 11_adjust_Rstar.py | T* → R* DS61 → re-escalar RS → re-analizar |
| 12 | 12_results.py | Periodos, corte basal, drift, peso sismico |

### Fase 4: Variante
| Paso | Script | Que hace |
|------|--------|----------|
| 13 | 13_semirigid.py | Edificio1_SemiRigido.edb (sin diafragma) |

## Bug principal corregido (v3)

**Problema**: La API reportaba ~2060 elementos creados, pero ETABS los mostraba vacios.

**Causa**: `Helper.CreateObject()` lanzaba una instancia INVISIBLE de ETABS.
Los elementos se creaban en la instancia fantasma, no en la ventana que el usuario veia.

**Fix**:
1. Priorizar `GetActiveObject` (conecta al ETABS visible)
2. Si necesita crear instancia nueva, FORZAR `obj.Visible = True`
3. Verificacion post-creacion en cada paso de geometria
4. Paso 7b aborta si no se verifican elementos

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

1. Abrir Edificio1.edb
2. Define > Diaphragm Eccentricity Overrides
3. Para cada piso, shift CM:
   - Sismo X: ΔCM_y = ±0.05 × 13.821m = ±0.691m
   - Sismo Y: ΔCM_x = ±0.05 × 38.505m = ±1.925m
4. Crear RS cases separados
5. Correr analisis

## Archivos generados

| Archivo | Contenido |
|---------|-----------|
| Edificio1.edb | Modelo con diafragma rigido, espectro con R* |
| Edificio1_SemiRigido.edb | Modelo sin diafragma rigido |
| espectro_nch433.txt | Espectro para importar manual (T vs Sa/g) |

## Si algo falla

### Espectro no se define via API
Define > Functions > Response Spectrum > From File > espectro_nch433.txt

### Mass source no se define via API
Define > Mass Source > Self Mass: SI + TERP: 1.0 + SCP: 0.25

### Conexion falla
1. `python diag.py` — ver que metodos funcionan
2. Matar TODOS los ETABS, abrir solo v19, esperar 20s
3. Si registry apunta a v21: `"...\ETABS 19\ETABS.exe" /regserver` como admin

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
