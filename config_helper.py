"""
config_helper.py — Conexion a ETABS via COM.

COMPATIBLE CON DUAL-INSTALL (v19 + v21).

FIXES:
1. Limpia comtypes.gen al inicio (previene type library stale de otra version)
2. Mantiene TODOS los objetos COM en globales (previene garbage collection)
3. Multiples metodos de conexion con reintentos
4. Diagnostico claro si falla
"""
import os
import sys
import shutil

# ====================================================================
# PASO 0: Limpiar cache comtypes ANTES de importar comtypes.client.
# Si comtypes.gen tiene type library de ETABS 21 y conectamos a v19,
# los metodos COM fallan con "Puntero no valido" por vtable mismatch.
# ====================================================================
for _sp in sys.path:
    _gen = os.path.join(_sp, 'comtypes', 'gen')
    if os.path.isdir(_gen):
        for _f in os.listdir(_gen):
            if _f in ('__init__.py', '__pycache__'):
                continue
            _p = os.path.join(_gen, _f)
            try:
                shutil.rmtree(_p) if os.path.isdir(_p) else os.remove(_p)
            except OSError:
                pass
        break

import comtypes.client
import time

# ====================================================================
# Constantes de unidades ETABS
# ====================================================================
TONF_M_C = 9
KGF_M_C = 6
KGF_CM_C = 7

# Rutas ETABS (PC lab UCN)
ETABS19_EXE = r"C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"
ETABS21_EXE = r"C:\Program Files\Computers and Structures\ETABS 21\ETABS.exe"
ETABS19_TLB = r"C:\Program Files\Computers and Structures\ETABS 19\ETABSv1.tlb"

# ====================================================================
# PASO 1: Cargar type library de ETABS 19 EXPLICITAMENTE.
# Si no se hace esto, comtypes genera la TLB de v21 (registrada en COM),
# y las firmas de metodos como SetStories no coinciden con v19.
# ====================================================================
if os.path.exists(ETABS19_TLB):
    try:
        comtypes.client.GetModule(ETABS19_TLB)
    except Exception:
        pass  # Si falla, usara la TLB auto-generada

# ====================================================================
# Estado global — mantener TODAS las refs COM vivas (evitar GC).
# Si helper/obj se garbage-collectan, SapModel queda invalido.
# ====================================================================
_helper_ref = None
_etabs_obj = None
_model = None


def _test_model(m):
    """Verifica que SapModel funciona (no solo que existe)."""
    try:
        m.GetPresentUnits()
        return True
    except Exception:
        return False


def get_model(retries=5, wait=5):
    """Conectar a ETABS. Intenta multiples metodos, reintenta si no esta listo."""
    global _model, _etabs_obj, _helper_ref

    if _model is not None:
        return _model

    last_err = None

    for attempt in range(1, retries + 1):

        # --- Metodo 1: GetActiveObject (PRIORITARIO) ---
        # Conecta al ETABS ya corriendo. No spawna procesos extra.
        # Confirmado que funciona en PC lab con comtypes.gen limpio.
        try:
            obj = comtypes.client.GetActiveObject('CSI.ETABS.API.ETABSObject')
            m = obj.SapModel
            if _test_model(m):
                m.SetPresentUnits(TONF_M_C)
                _etabs_obj = obj  # KEEP ALIVE
                _model = m
                print("[OK] ETABS conectado via GetActiveObject (tonf_m_C)")
                return _model
        except Exception as e:
            last_err = e

        # --- Metodo 2: Helper.GetObject (ruta especifica) ---
        # Conecta al ETABS de la ruta indicada (v19 o v21).
        for exe_path in [ETABS19_EXE, ETABS21_EXE]:
            if not os.path.exists(exe_path):
                continue
            try:
                helper = comtypes.client.CreateObject('ETABSv1.Helper')
                import comtypes.gen.ETABSv1 as ETABSv1
                helper = helper.QueryInterface(ETABSv1.cHelper)
                obj = helper.GetObject(exe_path)
                if obj is None:
                    continue
                m = obj.SapModel
                if _test_model(m):
                    m.SetPresentUnits(TONF_M_C)
                    _helper_ref = helper  # KEEP ALIVE
                    _etabs_obj = obj      # KEEP ALIVE
                    _model = m
                    ver = "19" if "19" in exe_path else "21"
                    print(f"[OK] ETABS conectado via Helper.GetObject v{ver} (tonf_m_C)")
                    return _model
            except Exception as e:
                last_err = e

        # --- Metodo 3: Helper.CreateObject (lanza nueva instancia v19) ---
        # Solo si nada mas funciona. Lanza un nuevo ETABS.
        for exe_path in [ETABS19_EXE, ETABS21_EXE]:
            if not os.path.exists(exe_path):
                continue
            try:
                helper = comtypes.client.CreateObject('ETABSv1.Helper')
                import comtypes.gen.ETABSv1 as ETABSv1
                helper = helper.QueryInterface(ETABSv1.cHelper)
                obj = helper.CreateObject(exe_path)
                try:
                    obj.ApplicationStart()
                except Exception:
                    pass
                time.sleep(5)
                m = obj.SapModel
                if _test_model(m):
                    m.SetPresentUnits(TONF_M_C)
                    _helper_ref = helper
                    _etabs_obj = obj
                    _model = m
                    ver = "19" if "19" in exe_path else "21"
                    print(f"[OK] ETABS conectado via Helper.CreateObject v{ver} (tonf_m_C)")
                    return _model
            except Exception as e:
                last_err = e

        # --- Metodo 4: CreateObject (ultimo recurso, spawna v21) ---
        try:
            obj = comtypes.client.CreateObject('CSI.ETABS.API.ETABSObject')
            m = obj.SapModel
            if _test_model(m):
                m.SetPresentUnits(TONF_M_C)
                _etabs_obj = obj
                _model = m
                print("[OK] ETABS conectado via CreateObject (tonf_m_C)")
                return _model
        except Exception as e:
            last_err = e

        if attempt < retries:
            print(f"  Intento {attempt}/{retries} fallido, reintentando en {wait}s...")
            time.sleep(wait)

    print(f"\n[ERROR] No se pudo conectar a ETABS: {last_err}")
    print("\nSoluciones:")
    print("  1. Cerrar TODO ETABS (taskkill /F /IM ETABS.exe)")
    print("  2. Abrir ETABS (v19 o v21), esperar a que cargue completamente")
    print("  3. python run_all.py")
    print("")
    print("  Si sigue fallando, probar registrar ETABS 19 como admin:")
    print(f'  "{ETABS19_EXE}" /regserver')
    sys.exit(1)


def set_units_kgf_cm(m):
    """Cambiar a kgf/cm/C."""
    m.SetPresentUnits(KGF_CM_C)


def set_units_tonf_m(m):
    """Cambiar a tonf/m/C."""
    m.SetPresentUnits(TONF_M_C)
