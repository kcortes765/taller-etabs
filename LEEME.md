# Taller ETABS — Edificio 1 (20 pisos, muros)
# INSTRUCCIONES PARA PC LAB (sin git)

## Requisitos PC Lab
- Python 3.12 (ya instalado en C:\Users\Civil\...)
- ETABS 19 (instalado)
- Paquete: `pip install comtypes` (si no esta)

## Como usar

```powershell
# 1. Copiar TODA esta carpeta a C:\Users\Civil\Desktop\ta\
#    (USB, Drive, lo que sea)

# 2. Abrir ETABS 19 → ESPERAR a que cargue completamente
#    (pantalla principal visible, NO la splash screen)
#    Esperar minimo 15 segundos despues de abrir

# 3. Limpiar cache comtypes (solo si hay errores raros):
Remove-Item "C:\Users\Civil\AppData\Local\Programs\Python\Python312\Lib\site-packages\comtypes\gen\*" -Recurse -Force

# 4. Correr TODO de una vez:
cd C:\Users\Civil\Desktop\ta
python run_all.py

# O paso a paso (para debug):
python 00_test_api.py          # TEST: verifica conexion
python 01_init_model.py        # Modelo vacio + 20 pisos
python 02_materials_sections.py # G30, A630-420H, secciones
python 03_walls.py              # Muros en todos los pisos
python 04_beams.py              # Vigas en todos los pisos
python 05_slabs.py              # Losas en todos los pisos
python 06_loads.py              # Patrones + cargas
python 07_diaphragm_supports.py # Diafragma rigido + empotramientos
python 08_spectrum_cases.py     # Espectro, modal, RS, combos
```

## Archivos (12 scripts)
| Archivo | Que hace |
|---------|----------|
| config.py | Datos completos Ed.1: grilla, pisos, materiales, muros, vigas, cargas |
| config_helper.py | Conexion ETABS COM (3 metodos + reintentos) |
| 00_test_api.py | Diagnostico: prueba todos los metodos API |
| 01_init_model.py | Modelo vacio + 20 pisos (3.4m + 19×2.6m = 52.8m) |
| 02_materials_sections.py | G30, A630-420H, VI20x60, MHA30, MHA20, Losa15 |
| 03_walls.py | ~50 muros/piso × 20 pisos (~1000 muros) |
| 04_beams.py | ~22 vigas/piso × 20 pisos |
| 05_slabs.py | 35 paños/piso × 20 pisos |
| 06_loads.py | PP, SCP, SCT, TERP, TERT, SEx, SEy + cargas en losas |
| 07_diaphragm_supports.py | Diafragma rigido DR + empotramientos z=0 |
| 08_spectrum_cases.py | Espectro NCh433+DS61, modal 60 modos, RS, 8 combos NCh3171 |
| run_all.py | Ejecuta todo en orden |

## Error comun: "Puntero no valido"
**Causa**: ETABS no termino de cargar, o se uso CreateObject en vez de GetActiveObject.
**Fix**: Ya corregido en config_helper.py (prueba 3 metodos + reintenta 5 veces).
Si sigue fallando:
1. Cerrar TODO (ETABS + Python)
2. Limpiar comtypes/gen (paso 3 arriba)
3. Abrir ETABS, esperar 15-20 seg
4. Correr `python 00_test_api.py` primero

## Despues de correr los scripts
1. **Vista 3D**: verificar que el edificio se ve bien
2. **Peso sismico**: verificar ~1 tonf/m2 (Display > Story Response Plots)
3. **R***: ajustar segun T* (tras primer Run Analysis). El espectro esta elastico (R=1)
4. **Run Analysis**
5. **Guardar** como .EDB

## Que falta (manual en ETABS GUI)
- Verificar/ajustar mesh de muros si es necesario
- R* (factor de reduccion) — requiere T* del primer analisis
- Torsion accidental (3 metodos en Material Apoyo Taller 2026.pdf)
- Section Designer para diagramas P-M
- SAP2000 para curvas M-φ

## Edificio 1 — Datos clave
- 20 pisos: P1=3.4m, P2-P20=2.6m → H=52.8m
- 17 ejes X (numericos) + 6 ejes Y (A-F)
- Muros 30cm (ejes 1,3,4,5,7,12,13,14,16,17 + eje C entre 3-6 y 10-14)
- Muros 20cm (resto)
- Vigas VI20/60 en ejes A, B, F + interiores
- Losa 15cm, inercia reducida al 25%
- G30 (f'c=30 MPa), A630-420H (fy=420 MPa)
- Zona 3, Ao=0.4g, Suelo C, Cat.II, Ro=11
