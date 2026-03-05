"""
config_helper.py — Conexion a ETABS via COM.

COMPATIBLE CON DUAL-INSTALL (v19 + v21).

FIX v3 (2026-03-05):
- NUNCA crear instancias invisibles — causa principal del bug "geometria fantasma"
- Si CreateObject es necesario, FORZAR visibilidad (ApplicationStart + Visible=True)
- Diagnostico automatico tras conexion (version, archivo, elementos)
- Funciones de verificacion y refresco de vista
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
# ====================================================================
if os.path.exists(ETABS19_TLB):
    try:
        comtypes.client.GetModule(ETABS19_TLB)
    except Exception:
        pass

# ====================================================================
# Estado global — mantener TODAS las refs COM vivas (evitar GC).
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


def diagnose(m):
    """Imprimir diagnostico de la conexion actual."""
    print("  --- Diagnostico conexion ---")
    try:
        fname = m.GetModelFilename()
        print(f"  Archivo modelo: {fname or '(sin guardar)'}")
    except Exception:
        print("  Archivo modelo: (no disponible)")

    for obj_type, getter in [('Areas', 'AreaObj'), ('Frames', 'FrameObj'), ('Points', 'PointObj')]:
        try:
            result = getattr(m, getter).GetNameList()
            if isinstance(result, (list, tuple)):
                count = result[0] if isinstance(result[0], int) else 0
            else:
                count = '?'
            print(f"  {obj_type}: {count}")
        except Exception:
            pass
    print("  ---")


def verify_elements(m):
    """Verificar que existen elementos en el modelo. Retorna dict con conteos."""
    counts = {}
    for obj_type, getter in [('areas', 'AreaObj'), ('frames', 'FrameObj'), ('points', 'PointObj')]:
        try:
            result = getattr(m, getter).GetNameList()
            if isinstance(result, (list, tuple)):
                counts[obj_type] = result[0] if isinstance(result[0], int) else 0
            else:
                counts[obj_type] = 0
        except Exception:
            counts[obj_type] = 0
    return counts


def refresh_view(m):
    """Forzar refresco de la vista ETABS."""
    try:
        m.View.RefreshView(0, False)
    except Exception:
        try:
            m.View.RefreshView()
        except Exception:
            pass


def get_model(retries=3, wait=5):
    """Conectar a ETABS EXISTENTE. No crea instancias invisibles.

    Orden de prioridad:
    1. GetActiveObject — conecta al ETABS en el Running Object Table
    2. Helper.GetObject(v19) — conecta al ETABS v19 ya corriendo
    3. Helper.GetObject(v21) — conecta al ETABS v21 ya corriendo
    4. Helper.CreateObject(v19) — ULTIMO RECURSO, crea instancia VISIBLE

    IMPORTANTE: El metodo 4 solo se usa si nada mas funciona, y FUERZA
    visibilidad para evitar el bug de instancias fantasma.
    """
    global _model, _etabs_obj, _helper_ref

    if _model is not None:
        return _model

    last_err = None

    for attempt in range(1, retries + 1):
        # --- Metodo 1: GetActiveObject ---
        try:
            obj = comtypes.client.GetActiveObject('CSI.ETABS.API.ETABSObject')
            m = obj.SapModel
            if _test_model(m):
                m.SetPresentUnits(TONF_M_C)
                _etabs_obj = obj
                _model = m
                print("[OK] ETABS conectado via GetActiveObject")
                diagnose(m)
                return _model
        except Exception as e:
            last_err = e
            if attempt == 1:
                print(f"  GetActiveObject: {e}")

        # --- Metodo 2: Helper.GetObject (conecta a ETABS ya corriendo) ---
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
                    _helper_ref = helper
                    _etabs_obj = obj
                    _model = m
                    ver = "19" if "19" in exe_path else "21"
                    print(f"[OK] ETABS conectado via Helper.GetObject v{ver}")
                    diagnose(m)
                    return _model
            except Exception as e:
                last_err = e

        if attempt < retries:
            print(f"  Intento {attempt}/{retries} fallido, reintentando en {wait}s...")
            time.sleep(wait)

    # --- Metodo 3: Helper.CreateObject — ULTIMO RECURSO ---
    # Crea nueva instancia pero la hace VISIBLE para evitar el bug fantasma
    print("\n  [WARN] No se pudo conectar a ETABS existente.")
    print("  Creando nueva instancia VISIBLE de ETABS...")

    for exe_path in [ETABS19_EXE, ETABS21_EXE]:
        if not os.path.exists(exe_path):
            continue
        try:
            helper = comtypes.client.CreateObject('ETABSv1.Helper')
            import comtypes.gen.ETABSv1 as ETABSv1
            helper = helper.QueryInterface(ETABSv1.cHelper)
            obj = helper.CreateObject(exe_path)

            # *** CRITICO: Forzar visibilidad ***
            try:
                obj.ApplicationStart()
            except Exception:
                pass
            try:
                obj.Visible = True
            except Exception:
                pass

            print("  Esperando que ETABS cargue (15s)...")
            time.sleep(15)

            m = obj.SapModel
            if _test_model(m):
                m.SetPresentUnits(TONF_M_C)
                _helper_ref = helper
                _etabs_obj = obj
                _model = m
                ver = "19" if "19" in exe_path else "21"
                print(f"[OK] ETABS conectado via Helper.CreateObject v{ver} (instancia nueva)")
                print("  >>> Verifica que la ventana de ETABS sea visible <<<")
                diagnose(m)
                return _model
        except Exception as e:
            last_err = e
            ver = "19" if "19" in exe_path else "21"
            print(f"  Helper.CreateObject v{ver}: {e}")

    # --- Nada funciono ---
    print(f"\n[ERROR] No se pudo conectar a ETABS: {last_err}")
    print("\nSOLUCIONES:")
    print("  1. Cerrar TODO ETABS:")
    print("     taskkill /F /IM ETABS.exe")
    print("  2. Abrir ETABS 19, esperar a que cargue completamente (20s+)")
    print("  3. python run_all.py")
    print("")
    print("  Si sigue fallando, registrar ETABS 19 como admin:")
    print(f'  "{ETABS19_EXE}" /regserver')
    sys.exit(1)


def set_units_kgf_cm(m):
    """Cambiar a kgf/cm/C."""
    m.SetPresentUnits(KGF_CM_C)


def set_units_tonf_m(m):
    """Cambiar a tonf/m/C."""
    m.SetPresentUnits(TONF_M_C)
