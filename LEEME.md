# Taller ETABS — Edificio 1 (20 pisos, muros)
# INSTRUCCIONES PARA PC LAB (sin git)

## Descargar

```powershell
cd C:\Users\Civil\Desktop
Invoke-WebRequest -Uri "https://github.com/kcortes765/taller-etabs/archive/refs/heads/master.zip" -OutFile ta.zip
Expand-Archive ta.zip -DestinationPath ta -Force
Copy-Item ta\taller-etabs-master\* ta\ -Force -Recurse
Remove-Item ta\taller-etabs-master -Recurse -Force
Remove-Item ta.zip
cd ta
```

## Requisitos
- Python 3.12 (ya instalado)
- `pip install comtypes` (si no esta)
- ETABS 19

## IMPORTANTE: Dual-install v19 + v21

El PC lab tiene ETABS 19 y 21. El problema:
- `CreateObject('CSI.ETABS.API.ETABSObject')` SIEMPRE lanza ETABS 21
- Los scripts usan `Helper.GetObject(ruta_v19)` que conecta al ETABS 19 abierto

## Como usar

```powershell
# 1. MATAR TODO ETABS (19 y 21)
Get-Process ETABS -EA SilentlyContinue | Stop-Process -Force
Start-Sleep 3

# 2. LIMPIAR cache comtypes
Remove-Item "C:\Users\Civil\AppData\Local\Programs\Python\Python312\Lib\site-packages\comtypes\gen\*" -Recurse -Force

# 3. ABRIR solo ETABS 19
Start-Process "C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"

# 4. ESPERAR 20 segundos (que cargue completamente)
Start-Sleep 20

# 5. VERIFICAR que solo v19 corre:
Get-Process ETABS | Select-Object Id, Path
# Debe mostrar SOLO la ruta de ETABS 19. Si aparece v21, matarla:
# Get-Process ETABS | Where-Object {$_.Path -like "*21*"} | Stop-Process -Force

# 6. DIAGNOSTICO (primera vez):
cd C:\Users\Civil\Desktop\ta
python diag.py

# 7. TEST (verifica que API funciona):
python 00_test_api.py

# 8. EJECUTAR TODO:
python run_all.py
```

## Si falla la conexion

1. **"Puntero no valido"**: ETABS no cargo o hay conflicto v21
   - Matar TODO, limpiar cache, re-abrir solo v19, esperar 20s
2. **ETABS 21 sigue apareciendo**: `CreateObject` lo lanza
   - Los scripts ya NO usan CreateObject, pero si limpiaste cache y ETABS 21 aparece, matarlo
3. **Nada funciona**: Correr `python diag.py` y copiar resultado completo

## Archivos
| Archivo | Que hace |
|---------|----------|
| diag.py | Diagnostico completo (correr primero si hay problemas) |
| config_helper.py | Conexion ETABS 19 via Helper.GetObject (NO lanza v21) |
| 00_test_api.py | Test de todos los metodos API |
| 01-08_*.py | Pasos del edificio |
| run_all.py | Ejecuta todo en orden |
| config.py | Datos geometria/cargas del Edificio 1 |

## Despues de correr los scripts
1. Vista 3D: verificar edificio
2. Peso sismico: ~1 tonf/m2
3. R*: ajustar segun T* (espectro esta elastico)
4. Run Analysis
5. Guardar como .EDB
