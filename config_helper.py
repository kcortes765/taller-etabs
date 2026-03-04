"""
config_helper.py — Conexion a ETABS 19 (PC lab con v19 + v21 instalados).

PROBLEMA: CreateObject('CSI.ETABS.API.ETABSObject') siempre lanza ETABS 21
porque v21 esta registrada como COM server default en Windows.

SOLUCION: Usar Helper.GetObject(ruta_exe) que conecta al ETABS 19 ya abierto.
NUNCA usar CreateObject (lanza v21).
"""
import comtypes.client
import subprocess
import sys
import time
import os

_model = None

TONF_M_C = 9
KGF_M_C = 6
KGF_CM_C = 7

# Ruta ETABS 19 en PC lab UCN
ETABS19_EXE = r"C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"


def _kill_etabs21():
    """Mata procesos ETABS 21 que interfieren."""
    try:
        r = subprocess.run(
            ['powershell', '-Command',
             'Get-Process ETABS -EA SilentlyContinue | '
             'Where-Object {$_.Path -like \"*21*\"} | '
             'Stop-Process -Force -PassThru | '
             'Measure-Object | Select-Object -Expand Count'],
            capture_output=True, text=True, timeout=10
        )
        n = r.stdout.strip()
        if n and int(n) > 0:
            print(f"  [!] Cerrados {n} procesos ETABS 21")
            time.sleep(2)
    except Exception:
        pass


def _is_etabs19_running():
    """Verifica que ETABS 19 esta corriendo."""
    try:
        r = subprocess.run(
            ['powershell', '-Command',
             '(Get-Process ETABS -EA SilentlyContinue | '
             'Where-Object {$_.Path -like \"*19*\"}).Count'],
            capture_output=True, text=True, timeout=10
        )
        return int(r.stdout.strip() or '0') > 0
    except Exception:
        return False


def _connect_helper_getobject():
    """Conectar via Helper.GetObject(ruta) — metodo correcto para dual-install."""
    helper = comtypes.client.CreateObject('ETABSv1.Helper')
    import comtypes.gen.ETABSv1 as ETABSv1
    helper = helper.QueryInterface(ETABSv1.cHelper)
    obj = helper.GetObject(ETABS19_EXE)  # RUTA al .exe, NO ProgID
    m = obj.SapModel
    m.GetPresentUnits()  # test — lanza excepcion si SapModel es null
    return m


def _connect_getactiveobject():
    """Conectar via GetActiveObject — funciona si ETABS 19 se registro en ROT."""
    obj = comtypes.client.GetActiveObject('CSI.ETABS.API.ETABSObject')
    m = obj.SapModel
    m.GetPresentUnits()
    return m


def get_model(retries=5, wait=4):
    """Conectar al ETABS 19 que esta corriendo."""
    global _model
    if _model is not None:
        return _model

    # Paso 0: Matar ETABS 21
    _kill_etabs21()

    # Verificar ETABS 19
    if not _is_etabs19_running():
        print("[ERROR] ETABS 19 no esta corriendo.")
        print(f"  Abrir: {ETABS19_EXE}")
        print("  Esperar a que cargue, luego re-ejecutar.")
        sys.exit(1)

    methods = [
        ('Helper.GetObject', _connect_helper_getobject),
        ('GetActiveObject',  _connect_getactiveobject),
    ]

    for attempt in range(1, retries + 1):
        for name, func in methods:
            try:
                _model = func()
                _model.SetPresentUnits(TONF_M_C)
                print(f"[OK] Conectado a ETABS 19 via {name} (tonf_m_C)")
                return _model
            except Exception as e:
                if attempt <= 2:
                    print(f"  {name}: {e}")

        if attempt < retries:
            print(f"  Intento {attempt}/{retries}... esperando {wait}s")
            time.sleep(wait)

    print(f"\n[ERROR] No se pudo conectar despues de {retries} intentos.")
    print("Probar:")
    print("  1. Cerrar TODO (ETABS + Python)")
    print("  2. powershell: Remove-Item comtypes\\gen\\* (limpiar cache)")
    print("  3. Abrir SOLO ETABS 19, esperar 20 seg")
    print("  4. python diag.py  (diagnostico)")
    sys.exit(1)


def set_units_kgf_cm(m):
    m.SetPresentUnits(KGF_CM_C)

def set_units_tonf_m(m):
    m.SetPresentUnits(TONF_M_C)
