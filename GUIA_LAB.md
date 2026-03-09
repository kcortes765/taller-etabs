# Guía de Ejecución — PC Laboratorio UCN

## Resumen rápido (todo el flujo)

```
PowerShell Admin → .\lab_inicio.ps1   ← setup automático
python diag.py                         ← verificar conexión
python run_all.py                      ← ejecutar todo
[ETABS: Auto-Mesh manual si 07c falla]
[ETABS: P-Delta manual]
python 12_results.py                   ← ver resultados finales
```

---

## PASO 0 — Antes de empezar

Sentarse frente al PC. **No abrir ETABS todavía.**

---

## PASO 1 — Ejecutar lab_inicio.ps1

```powershell
# Click derecho en PowerShell → "Run as administrator"
cd C:\Users\Civil\Desktop
.\lab_inicio.ps1
```

El script hace automáticamente:
- Mata todos los ETABS residuales
- Limpia cache comtypes (evita el bug v19/v21)
- Abre ETABS 19 y espera 25s
- Descarga el ZIP de GitHub y lo extrae en `Desktop\ta\`
- Verifica Python y comtypes

**Si algo falla en el script:** Ver sección "Problemas" al final.

---

## PASO 2 — Verificar conexión con diag.py

```powershell
cd C:\Users\Civil\Desktop\ta
python diag.py
```

### Lo que debes ver (BUENO):
```
[A-GetActiveObject] OK
  Units=12 (Ton_m_C) o similar, File=(vacio), Visible=True

RESUMEN:
  FUNCIONAN: A-GetActiveObject
  config_helper.py usara: A-GetActiveObject
```

### Lo que es problemático (MALO):
```
[A-GetActiveObject] FAIL
[WARN] GetActiveObject falla pero CreateObject funciona.
ETABS NO esta en el Running Object Table.
```
→ **Solución**: Cerrar ETABS, volver a abrirlo, esperar 30s, repetir `python diag.py`.

---

## PASO 3 — Ejecutar pipeline

```powershell
python run_all.py
```

### ⚠️ REGLA CRÍTICA mientras corre:
**NO HACER CLIC en la ventana de ETABS.**

Si ETABS dice "(Not Responding)" → es normal mientras mallá o analiza → esperar.

### Qué verás en consola (normal):

```
FASE 1: GEOMETRIA
  Paso 1:  Inicializar modelo y pisos    ... [OK]
  Paso 2:  Materiales y secciones        ... [OK]
  Paso 3:  Dibujar muros                 ... OK: 48 muros x 20 pisos
  Paso 4:  Dibujar vigas                 ... OK
  Paso 5:  Dibujar losas                 ... OK
  Paso 6:  Patrones y cargas             ... [OK]
  Paso 7:  Diafragma + empotramientos    ... [OK]
  Paso 7b: VERIFICACION + Checkpoint     ... stories OK, Areas: 1660, Frames: 400
  Paso 7c: Auto-Mesh muros y losas       ... [OK] 1660/1660 areas
```

### Si 07b dice "MODELO VACIO" → ABORTA automáticamente:
```
[ERROR CRITICO] EL MODELO ESTA VACIO!
ABORTANDO pipeline
```
→ Solución: `taskkill /F /IM ETABS.exe` → abrir ETABS 19 → esperar 30s → repetir.

---

## PASO 4 — Intervenciones manuales (durante/después del pipeline)

### 4a. Auto-Mesh (si paso 7c falló)

Cuando la consola diga que 07c falló, hacer **en ETABS**:

```
Ctrl+A                              ← seleccionar todo

Assign > Shell > Wall Auto Mesh Options
  ☑ Auto Rectangular Mesh
  Max Element Size: 1.0
  ☑ Add Restraint Points from Lines
  → OK

Assign > Shell > Floor Auto Mesh Options
  ☑ Auto Rectangular Mesh
  Max Element Size: 1.0
  → OK

File > Save
```

**¿Cómo verificar?** La malla debería verse en la vista 3D como una cuadrícula de ~1m en los muros.

### 4b. Espectro (si paso 8 falló)

```
Define > Functions > Response Spectrum > Add New Function
  Type: From File
  File: ta\espectro_nch433.txt
  Name: Espectro_NCh433
  Headers lines to skip: 0
  → OK
```

### 4c. Mass Source (si paso 8 lo saltó)

```
Define > Mass Source
  ☑ Element Self Mass
  Additional Masses from Loads:
  + TERP → Factor 1.0
  + SCP  → Factor 0.25
  → OK
```

---

## PASO 5 — Correr análisis (si paso 10 falló)

```
Analyze > Run Analysis (F5)
```

Esperar. Puede tardar 5-15 minutos para 20 pisos con 60 modos.

---

## PASO 6 — P-Delta (MANUAL — siempre)

Antes de extraer fuerzas para diseñar:

```
Define > P-Delta Options
  Type: Iterative - Based on Loads
  Load Combinations:
  + PP    → Factor 1.0
  + TERP  → Factor 1.0
  + TERT  → Factor 1.0
  + SCP   → Factor 0.25
  → OK

Analyze > Run Analysis
```

---

## PASO 7 — Ver resultados

```powershell
python 12_results.py
```

Revisa:
- **Periodos**: T1 ≈ 1.0–1.5s ← si da 0.2s, falta Auto-Mesh
- **Drift**: < 0.002 en CM, < 0.001 en extremos
- **Qmin**: el script avisa si hay que amplificar y da la escala nueva
- **Peso**: ~1 tonf/m²/piso (~10640 tonf total)

---

## Verificaciones en ETABS (ver en tablas)

```
Display > Show Tables > Analysis Output > Modal Participating Mass Ratios
  → T1, T2, T3 (periodos fundamentales)

Display > Show Tables > Analysis Output > Story Drifts
  → drift piso a piso (SEx y SEy)

Display > Show Tables > Building Output > Base Reactions
  → corte basal SEx y SEy (comparar con Qmin ~745 tonf)
```

---

## Valores esperados (referencia)

| Parámetro | Valor esperado | Si sale diferente |
|-----------|---------------|-------------------|
| T1 | 1.0–1.5s | < 0.5s → falta Auto-Mesh |
| T2 | 0.8–1.3s | — |
| Peso total | ~10640 tonf | < 5000 → mass source mal |
| Drift CM | < 0.002 | > 0.002 → revisar malla o espectro |
| Q_din X | > 745 tonf | < 745 → amplificar escala |

---

## Problemas frecuentes

### lab_inicio.ps1 no corre
```powershell
Set-ExecutionPolicy Bypass -Scope Process
.\lab_inicio.ps1
```

### Python no encontrado
```powershell
where python
# Si no aparece: buscar Python en C:\Python312\ o C:\Users\Civil\AppData\Local\Programs\Python\
```

### comtypes no instalado
```powershell
pip install comtypes
```

### GitHub no disponible (sin internet)
- Copiar la carpeta `ta\` desde USB al Desktop
- Continuar desde PASO 2

### ETABS 19 no está en la ruta estándar
Buscar en:
- `C:\Program Files\Computers and Structures\ETABS 19\`
- Actualizar `ETABS19_EXE` en `config_helper.py`
