# Contexto para Review — Pipeline ETABS API (Python + COM)

## Qué es
Pipeline de 13 scripts Python que automatiza la creación completa de un edificio de 20 pisos (muros de hormigón armado) en ETABS via la API COM (OAPI). Desde geometría hasta análisis sísmico y resultados.

**Repo**: https://github.com/kcortes765/taller-etabs (commit 89d810c)

## Stack
- Python 3.12 + comtypes (COM automation)
- ETABS v19 (CSI) — software de análisis estructural
- PC lab: dual-install v19 + v21 (causa conflictos COM)
- Sin dependencias externas más allá de comtypes

## Arquitectura

```
config.py              ← Datos del edificio (grillas, pisos, muros, vigas, cargas, params sísmicos)
config_helper.py       ← Conexión ETABS via COM (GetActiveObject / Helper)
run_all.py             ← Orquestador: 13 pasos en 4 fases

01_init_model.py       ← Crear modelo vacío + 20 pisos
02_materials_sections.py ← G30 (hormigón), A630-420H (acero), secciones
03_walls.py            ← ~960 muros (AreaObj.AddByCoord)
04_beams.py            ← ~400 vigas (FrameObj.AddByCoord)
05_slabs.py            ← ~700 losas (AreaObj.AddByCoord)
06_loads.py            ← Patrones de carga + asignación a losas
07_diaphragm_supports.py ← Diafragma rígido + empotramientos base
07b_save_checkpoint.py ← Verificación completa + guardar .edb

08_spectrum_cases.py   ← Espectro NCh433, caso modal, RS cases, combos
09_torsion_cases.py    ← Torsión accidental (caso a + caso b forma 2)
10_save_run.py         ← Guardar + correr análisis
11_adjust_Rstar.py     ← Leer T*, calcular R*, re-escalar, re-analizar
12_results.py          ← Mostrar periodos, corte basal, drift, peso
13_semirigid.py        ← Variante sin diafragma rígido
```

## Flujo de datos
1. `config.py` define TODA la geometría (coordenadas, secciones, cargas)
2. `config_helper.py` establece la conexión COM a ETABS (singleton `_model`)
3. Todos los scripts importan `get_model()` que retorna el mismo `SapModel` cacheado
4. `run_all.py` ejecuta cada script como módulo (`importlib.import_module`)

## Conexión COM — El Problema Principal

### Dual-install v19 + v21
El PC lab tiene ETABS 19 y 21. El registro COM (`HKCR\CSI.ETABS.API.ETABSObject`) puede apuntar a v21. Cuando el usuario abre v19 y el script usa `GetActiveObject`, puede fallar porque el CLSID en el ROT (Running Object Table) no coincide.

### Bug resuelto: Instancia fantasma
`Helper.CreateObject(exe_path)` lanza una NUEVA instancia de ETABS. Si no se fuerza `obj.Visible = True`, la instancia es invisible. El script creaba ~2060 elementos ahí, reportaba éxito, pero el usuario veía su ventana de ETABS vacía.

### Orden de conexión actual
1. `GetActiveObject('CSI.ETABS.API.ETABSObject')` — conecta al ROT
2. `Helper.GetObject(exe_path)` — conecta por ruta (v19 primero)
3. `Helper.CreateObject(exe_path)` — ÚLTIMO recurso, fuerza `Visible=True`

## Problemas conocidos que PUEDEN persistir

### 1. FuncRS.SetUser — firma COM inconsistente
La función para definir espectro de respuesta no se encuentra en algunos bindings COM:
- Con 5 args `(name, count, T[], Sa[], damp)` → excepción "falta DampRatio"
- Con 4 args `(name, count, T[], Sa[])` → excepción diferente
- **Workaround**: genera `espectro_nch433.txt` para importar manualmente

### 2. Mass source — API no disponible en todas las versiones
`PropMass.SetMassSource_1` y `MassSource.SetMassSource_1` pueden no existir.
**Workaround**: instrucciones para definir manualmente.

### 3. Modal case crash
`ModalEigen.SetCase('Modal')` puede causar access violation. ETABS crea caso 'MODAL' por defecto, así que solo ajustamos `SetNumberModes`.

### 4. SetRestraint retorno no estándar
Retorna `[(True,True,True,True,True,True), 0]` en vez de solo `0`. Se parsea con `_ret_ok()`.

### 5. GetCoordCartesian formato variable
Puede retornar `(x, y, z, ret)` o `(ret, x, y, z)` o `(x, y, z)` según versión/método de conexión.

## Parámetros del edificio

- **20 pisos**: h1=3.4m, h2-20=2.6m, H=52.8m
- **Planta**: 38.5m × 13.8m (~532 m²)
- **Grilla**: 17 ejes X × 6 ejes Y
- **Muros**: 30cm (ejes principales) y 20cm (secundarios)
- **Vigas**: VI20×60 G30 (J=0, práctica chilena)
- **Losas**: 15cm G30 (inercia reducida 25%)
- **Zona 3** (Antofagasta): Ao=0.4g, Suelo C, Ro=11

## Normativa aplicada
- NCh433 + DS61: diseño sísmico
- NCh3171: combinaciones de carga (8 combos básicos + 12 con torsión b2)
- ACI318-08/DS60: diseño hormigón armado
- Espectro: α(T) = (1 + 4.5·(To/T)^p) / (1 + (To/T)^3), Sa = S·Ao·α

## Qué revisar

1. **config_helper.py**: ¿La lógica de conexión COM es robusta? ¿El fallback a CreateObject con Visible=True resuelve el bug?
2. **Verificación post-creación** (03-05, 07b): ¿Es suficiente comparar GetNameList antes/después?
3. **08_spectrum_cases.py**: ¿Hay mejor forma de definir espectro via API COM?
4. **Robustez general**: ¿Hay edge cases que puedan hacer fallar silenciosamente?
5. **config.py**: ¿Los datos geométricos (muros, vigas, losas) son coherentes con un edificio de muros de 20 pisos?

## Cómo probar
No se puede probar sin ETABS instalado. El pipeline depende completamente de la API COM de CSI ETABS. El flujo es:
1. Abrir ETABS 19
2. `python diag.py` (verificar conexión)
3. `python run_all.py` (ejecutar pipeline completo)
4. Verificar visualmente en ETABS
