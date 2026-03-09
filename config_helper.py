"""
config_helper.py — Conexion y helpers base para ETABS 19 via COM.

ETABS 19 SOLAMENTE (PC lab UCN).

El flujo preferido es:
1. Adjuntar a una instancia visible ya abierta
2. Si no existe, lanzar ETABS 19 visiblemente y adjuntar

CSI documenta los enums de unidades en cSapModel.InitializeNewModel y eUnits:
  Ton_m_C = 12
  kgf_m_C = 8
  kgf_cm_C = 14
"""
import os
import sys
import shutil
import subprocess

# ====================================================================
# PASO 0: Limpiar cache comtypes ANTES de importar comtypes.client.
# Evita vtable mismatch si hay restos de sesiones anteriores.
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
# Constantes de unidades ETABS (CSI docs oficiales)
# ====================================================================
TONF_M_C = 12
KGF_M_C = 8
KGF_CM_C = 14

UNIT_NAMES = {
    TONF_M_C: 'Ton_m_C',
    KGF_M_C: 'kgf_m_C',
    KGF_CM_C: 'kgf_cm_C',
}

# Ruta ETABS 19 (PC lab UCN)
ETABS19_EXE = r"C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"
ETABS19_TLB = r"C:\Program Files\Computers and Structures\ETABS 19\ETABSv1.tlb"
AUTOSTART_WAIT_SECS = 25

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


def _unit_name(unit_code):
    return UNIT_NAMES.get(unit_code, f'Unknown({unit_code})')


def _ret_code(ret):
    if isinstance(ret, int):
        return ret
    if isinstance(ret, (list, tuple)) and ret:
        last = ret[-1]
        if isinstance(last, int):
            return last
    return None


def _looks_like_increasing(values):
    return all(values[i] <= values[i + 1] + 1e-9 for i in range(len(values) - 1))


def _parse_story_result(result):
    if not isinstance(result, (list, tuple)):
        return None

    values = list(result)
    names = None
    float_lists = []
    number_stories = None

    for value in values:
        if isinstance(value, int) and number_stories is None and value >= 0:
            number_stories = value
        elif isinstance(value, (list, tuple)) and value:
            if all(isinstance(x, str) for x in value) and names is None:
                names = list(value)
            else:
                try:
                    float_lists.append([float(x) for x in value])
                except (TypeError, ValueError):
                    pass

    if not names:
        return None

    elevations = None
    heights = None
    for data in float_lists:
        if len(data) != len(names):
            continue
        if elevations is None and _looks_like_increasing(data):
            elevations = data
            continue
        if heights is None:
            heights = data

    if elevations is None or heights is None:
        return None

    if names and names[0].lower() == 'base':
        names = names[1:]
        elevations = elevations[1:]
        heights = heights[1:]

    if number_stories is None:
        number_stories = len(names)

    return {
        'number_stories': int(number_stories),
        'story_names': names,
        'story_elevations': elevations,
        'story_heights': heights,
    }


def get_story_data(m):
    """Leer historias definidas en el modelo actual."""
    methods = [
        lambda: m.Story.GetStories(),
        lambda: m.Story.GetStories(0, [], [], [], [], [], [], []),
        lambda: m.Story.GetStories(0, [], [], [], [], [], [], [], 0),
    ]

    for func in methods:
        try:
            data = _parse_story_result(func())
            if data:
                return data
        except Exception:
            continue

    return None


def stories_match_expected(actual, expected_names, expected_heights, expected_elevations, tol=1e-3):
    """Comparar historias definidas con las esperadas."""
    if actual is None:
        return False, False

    names = actual.get('story_names', [])
    heights = actual.get('story_heights', [])
    elevations = actual.get('story_elevations', [])

    geometry_ok = (
        len(names) == len(expected_names)
        and len(heights) == len(expected_heights)
        and len(elevations) == len(expected_elevations)
        and all(abs(a - b) <= tol for a, b in zip(heights, expected_heights))
        and all(abs(a - b) <= tol for a, b in zip(elevations, expected_elevations))
    )
    names_ok = names == expected_names
    return geometry_ok, names_ok


def format_story_table(data, max_rows=6):
    if not data:
        return "  (sin informacion de stories)"

    lines = [
        f"  Stories: {data['number_stories']}",
        "  Muestra stories:",
    ]
    rows = zip(
        data.get('story_names', [])[:max_rows],
        data.get('story_heights', [])[:max_rows],
        data.get('story_elevations', [])[:max_rows],
    )
    for name, height, elevation in rows:
        lines.append(f"    {name:<10} h={height:.3f} m  z={elevation:.3f} m")
    if data.get('number_stories', 0) > max_rows:
        lines.append("    ...")
    return "\n".join(lines)


def unlock_model(m):
    """Desbloquear el modelo si ETABS lo dejo locked tras analizar."""
    methods = [
        lambda: m.SetModelIsLocked(False),
        lambda: m.SetModelIsLocked(False, False),
    ]
    for func in methods:
        try:
            ret = func()
            code = _ret_code(ret)
            if code in (None, 0):
                return True
        except Exception:
            continue
    return False


def _start_etabs19():
    """Lanzar ETABS 19 visible desde el ejecutable instalado."""
    if not os.path.exists(ETABS19_EXE):
        return False

    try:
        subprocess.Popen([ETABS19_EXE])
        print(f"[INFO] ETABS 19 no estaba disponible. Lanzando y esperando {AUTOSTART_WAIT_SECS}s...")
        time.sleep(AUTOSTART_WAIT_SECS)
        return True
    except Exception as exc:
        print(f"[WARN] No se pudo lanzar ETABS 19 automaticamente: {exc}")
        return False


def diagnose(m):
    """Imprimir diagnostico de la conexion actual."""
    print("  --- Diagnostico conexion ---")
    try:
        fname = m.GetModelFilename()
        print(f"  Archivo modelo: {fname or '(sin guardar)'}")
    except Exception:
        print("  Archivo modelo: (no disponible)")

    try:
        units = m.GetPresentUnits()
        print(f"  Unidades: {units} ({_unit_name(units)})")
    except Exception:
        pass

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

    story_data = get_story_data(m)
    if story_data:
        print(format_story_table(story_data))
    print("  ---")


def verify_elements(m):
    """Verificar elementos en el modelo. Retorna dict con conteos.
    Intenta GetNameList primero, luego Count como fallback.
    """
    counts = {}
    for obj_type, getter in [('areas', 'AreaObj'), ('frames', 'FrameObj'), ('points', 'PointObj')]:
        obj = getattr(m, getter, None)
        if obj is None:
            counts[obj_type] = 0
            continue
        # Metodo 1: GetNameList
        try:
            result = obj.GetNameList()
            if isinstance(result, (list, tuple)):
                counts[obj_type] = result[0] if isinstance(result[0], int) else 0
            else:
                counts[obj_type] = 0
            continue
        except Exception:
            pass
        # Metodo 2: Count (fallback para frames en algunos bindings v19)
        try:
            counts[obj_type] = obj.Count()
        except Exception:
            counts[obj_type] = 0
    return counts


def refresh_view(m):
    """Refresco de vista — deshabilitado para evitar freeze con modelos grandes."""
    pass


def get_model(retries=3, wait=5):
    """Conectar a ETABS 19 visible.

    Metodos en orden:
    1. GetActiveObject — conecta al ETABS en el Running Object Table
    2. Helper.GetObject(v19) — conecta al ETABS v19 ya corriendo
    3. Si no hay ETABS visible, lanzar ETABS 19 y reintentar ambos metodos
    """
    global _model, _etabs_obj, _helper_ref

    if _model is not None:
        return _model

    def _try_attach():
        last_error = None

        try:
            obj = comtypes.client.GetActiveObject('CSI.ETABS.API.ETABSObject')
            m = obj.SapModel
            if _test_model(m):
                m.SetPresentUnits(TONF_M_C)
                return ('GetActiveObject', None, obj, m)
        except Exception as exc:
            last_error = exc

        if os.path.exists(ETABS19_EXE):
            try:
                helper = comtypes.client.CreateObject('ETABSv1.Helper')
                import comtypes.gen.ETABSv1 as ETABSv1
                helper = helper.QueryInterface(ETABSv1.cHelper)
                obj = helper.GetObject(ETABS19_EXE)
                if obj is not None:
                    m = obj.SapModel
                    if _test_model(m):
                        m.SetPresentUnits(TONF_M_C)
                        return ('Helper.GetObject(v19)', helper, obj, m)
            except Exception as exc:
                last_error = exc

        return (None, None, None, last_error)

    last_err = None
    autostart_attempted = False

    for attempt in range(1, retries + 1):
        method, helper, obj, payload = _try_attach()
        if method is not None:
            _helper_ref = helper
            _etabs_obj = obj
            _model = payload
            print(f"[OK] ETABS conectado via {method}")
            diagnose(_model)
            return _model

        last_err = payload
        if attempt == 1 and last_err is not None:
            print(f"  Conexion inicial: {last_err}")

        if attempt == retries and not autostart_attempted:
            autostart_attempted = _start_etabs19()
            if autostart_attempted:
                extra_retries = max(2, retries)
                for extra_attempt in range(1, extra_retries + 1):
                    method, helper, obj, payload = _try_attach()
                    if method is not None:
                        _helper_ref = helper
                        _etabs_obj = obj
                        _model = payload
                        print(f"[OK] ETABS conectado via {method} tras autostart")
                        diagnose(_model)
                        return _model
                    last_err = payload
                    if extra_attempt < extra_retries:
                        time.sleep(wait)
                break

        if attempt < retries:
            print(f"  Intento {attempt}/{retries} fallido, reintentando en {wait}s...")
            time.sleep(wait)

    # --- Nada funciono ---
    print(f"\n[ERROR] No se pudo conectar a ETABS 19: {last_err}")
    print("\nSOLUCION:")
    print("  1. Cerrar TODO ETABS:  taskkill /F /IM ETABS.exe")
    print("  2. Abrir ETABS 19 manualmente (icono del escritorio)")
    print(f"  3. Esperar ~{AUTOSTART_WAIT_SECS}s hasta que cargue la ventana principal")
    print("  4. python run_all.py")
    print("")
    print("  Si sigue fallando, registrar COM como admin:")
    print(f'  "{ETABS19_EXE}" /regserver')
    sys.exit(1)


def set_units_kgf_cm(m):
    """Cambiar a kgf/cm/C."""
    m.SetPresentUnits(KGF_CM_C)


def set_units_tonf_m(m):
    """Cambiar a tonf/m/C."""
    m.SetPresentUnits(TONF_M_C)
