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
- ETABS 19 o 21

## NOTA: Dual-install v19 + v21

Los scripts intentan 4 metodos de conexion automaticamente:
1. CreateObject (version registrada en COM, generalmente v21)
2. GetActiveObject (ETABS que ya esta corriendo)
3. Helper.GetObject (conecta por ruta a v19 o v21)
4. Helper.CreateObject (lanza nueva instancia)

Ademas, limpian el cache de comtypes automaticamente al iniciar
(previene "Puntero no valido" por type library de otra version).

## Como usar

```powershell
# 1. MATAR TODO ETABS
Get-Process ETABS -EA SilentlyContinue | Stop-Process -Force
Start-Sleep 3

# 2. ABRIR ETABS (v19 o v21, el que necesites)
Start-Process "C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"

# 3. ESPERAR a que cargue (15-20 segundos)
Start-Sleep 20

# 4. DIAGNOSTICO (primera vez en un PC nuevo):
cd C:\Users\Civil\Desktop\ta
python diag.py

# 5. TEST (verifica que API funciona):
python 00_test_api.py

# 6. EJECUTAR TODO:
python run_all.py
```

## Si falla la conexion

1. **"Puntero no valido"**: Los scripts ya limpian comtypes/gen automaticamente.
   Si sigue fallando, cerrar TODO y reintentar.
2. **Nada funciona**: `python diag.py` y copiar resultado completo.
3. **Nuclear**: Registrar v19 como servidor COM (requiere admin):
   ```
   "C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe" /regserver
   ```

## Archivos
| Archivo | Que hace |
|---------|----------|
| diag.py | Diagnostico completo (correr primero si hay problemas) |
| config_helper.py | Conexion ETABS — 4 metodos, limpia cache, mantiene refs COM |
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
