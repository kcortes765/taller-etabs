"""
00_test_api.py — Diagnostico rapido de la API ETABS.

Prueba conexion y metodos principales.
IMPORTANTE: Mantiene refs COM en variables globales para evitar GC.

USO: Abrir ETABS, luego: python 00_test_api.py
"""
import os
import sys
import shutil

# Limpiar cache comtypes (previene type library stale)
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
        print("[OK] Cache comtypes limpiado")
        break

import comtypes.client
import time

ETABS19_EXE = r"C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"
ETABS21_EXE = r"C:\Program Files\Computers and Structures\ETABS 21\ETABS.exe"

# Globales para mantener COM refs vivas (evitar GC)
_G_HELPER = None
_G_OBJ = None


def _test_model(m):
    """Verifica que SapModel responde."""
    try:
        m.GetPresentUnits()
        return True
    except Exception:
        return False


def connect():
    """Prueba todos los metodos de conexion. Retorna (SapModel, metodo) o None."""
    global _G_HELPER, _G_OBJ

    methods_tried = []

    # 1. CreateObject
    try:
        obj = comtypes.client.CreateObject('CSI.ETABS.API.ETABSObject')
        m = obj.SapModel
        if _test_model(m):
            _G_OBJ = obj
            return m, "CreateObject"
        else:
            methods_tried.append(("CreateObject", "SapModel no responde"))
    except Exception as e:
        methods_tried.append(("CreateObject", str(e)[:80]))

    # 2. GetActiveObject
    try:
        obj = comtypes.client.GetActiveObject('CSI.ETABS.API.ETABSObject')
        m = obj.SapModel
        if _test_model(m):
            _G_OBJ = obj
            return m, "GetActiveObject"
        else:
            methods_tried.append(("GetActiveObject", "SapModel no responde"))
    except Exception as e:
        methods_tried.append(("GetActiveObject", str(e)[:80]))

    # 3. Helper.GetObject (v19, v21)
    for label, exe in [("v19", ETABS19_EXE), ("v21", ETABS21_EXE)]:
        if not os.path.exists(exe):
            continue
        try:
            helper = comtypes.client.CreateObject('ETABSv1.Helper')
            import comtypes.gen.ETABSv1 as ETABSv1
            helper = helper.QueryInterface(ETABSv1.cHelper)
            obj = helper.GetObject(exe)
            m = obj.SapModel
            if _test_model(m):
                _G_HELPER = helper
                _G_OBJ = obj
                return m, f"Helper.GetObject({label})"
            else:
                methods_tried.append((f"Helper.GetObject({label})", "SapModel no responde"))
        except Exception as e:
            methods_tried.append((f"Helper.GetObject({label})", str(e)[:80]))

    # 4. Helper.CreateObject (lanza nueva instancia)
    for label, exe in [("v19", ETABS19_EXE), ("v21", ETABS21_EXE)]:
        if not os.path.exists(exe):
            continue
        try:
            helper = comtypes.client.CreateObject('ETABSv1.Helper')
            import comtypes.gen.ETABSv1 as ETABSv1
            helper = helper.QueryInterface(ETABSv1.cHelper)
            obj = helper.CreateObject(exe)
            try:
                obj.ApplicationStart()
            except Exception:
                pass
            time.sleep(3)
            m = obj.SapModel
            if _test_model(m):
                _G_HELPER = helper
                _G_OBJ = obj
                return m, f"Helper.CreateObject({label})"
            else:
                methods_tried.append((f"Helper.CreateObject({label})", "SapModel no responde"))
        except Exception as e:
            methods_tried.append((f"Helper.CreateObject({label})", str(e)[:80]))

    print("\n  Resultados por metodo:")
    for name, err in methods_tried:
        print(f"    {name}: {err}")
    return None, None


def test():
    print("=== TEST API ETABS ===\n")

    result = connect()
    m, method = result

    if m is None:
        print("\n[ERROR] Ningun metodo de conexion funciono.")
        print("  1. Cerrar TODO ETABS")
        print("  2. Abrir ETABS (v19 o v21), esperar a que cargue")
        print("  3. Reintentar: python 00_test_api.py")
        sys.exit(1)

    print(f"[OK] Conectado via {method}\n")

    # --- Unidades ---
    try:
        u = m.GetPresentUnits()
        m.SetPresentUnits(9)  # tonf_m_C
        print(f"[OK] Unidades: {u} -> 9 (tonf_m_C)")
    except Exception as e:
        print(f"[FAIL] Unidades: {e}")

    # --- InitializeNewModel ---
    try:
        ret = m.InitializeNewModel(9)
        print(f"[OK] InitializeNewModel: ret={ret}")
    except Exception as e:
        print(f"[WARN] InitializeNewModel: {e}")

    # --- NewBlank ---
    try:
        ret = m.File.NewBlank()
        print(f"[OK] File.NewBlank: ret={ret}")
    except Exception as e:
        print(f"[WARN] File.NewBlank: {e}")

    # --- Stories ---
    try:
        ret = m.Story.SetStories(
            ['T1', 'T2'], [0.0, 3.0, 6.0], [3.0, 3.0],
            [True, True], ['', ''], [False, False], [0.0, 0.0])
        print(f"[OK] Story.SetStories: ret={ret}")
    except Exception as e:
        print(f"[FAIL] Story.SetStories: {e}")

    # --- Material ---
    try:
        ret = m.PropMaterial.SetMaterial('TM', 2)
        print(f"[OK] PropMaterial.SetMaterial: ret={ret}")
    except Exception as e:
        print(f"[FAIL] PropMaterial.SetMaterial: {e}")

    # --- Wall ---
    try:
        ret = m.PropArea.SetWall('TW', 1, 1, 'TM', 0.30)
        print(f"[OK] PropArea.SetWall(5p): ret={ret}")
    except Exception as e:
        print(f"[FAIL] SetWall(5p): {e}")
        try:
            ret = m.PropArea.SetWall('TW', 1, 'TM', 0.30)
            print(f"[OK] SetWall(4p): ret={ret}")
        except Exception as e2:
            print(f"[FAIL] SetWall(4p): {e2}")

    # --- Slab ---
    try:
        ret = m.PropArea.SetSlab('TS', 0, 1, 'TM', 0.15)
        print(f"[OK] PropArea.SetSlab: ret={ret}")
    except Exception as e:
        print(f"[FAIL] PropArea.SetSlab: {e}")

    # --- Frame ---
    try:
        ret = m.PropFrame.SetRectangle('TF', 'TM', 0.60, 0.20)
        print(f"[OK] PropFrame.SetRectangle: ret={ret}")
    except Exception as e:
        print(f"[FAIL] PropFrame.SetRectangle: {e}")

    # --- AreaObj ---
    try:
        r = m.AreaObj.AddByCoord(4, [0, 1, 1, 0], [0, 0, 0, 0], [0, 0, 3, 3], '', 'TW', '', 'Global')
        print(f"[OK] AreaObj.AddByCoord: {r}")
    except Exception as e:
        print(f"[FAIL] AreaObj.AddByCoord: {e}")

    # --- FrameObj ---
    try:
        r = m.FrameObj.AddByCoord(0, 0, 3, 1, 0, 3, '', 'TF', '', 'Global')
        print(f"[OK] FrameObj.AddByCoord: {r}")
    except Exception as e:
        print(f"[FAIL] FrameObj.AddByCoord: {e}")

    # --- LoadPatterns ---
    try:
        ret = m.LoadPatterns.Add('TL', 1, 0, True)
        print(f"[OK] LoadPatterns.Add: ret={ret}")
    except Exception as e:
        print(f"[FAIL] LoadPatterns.Add: {e}")

    # --- FuncRS ---
    try:
        r = m.Func.FuncRS.SetUser('TRS', 3, [0.0, 1.0, 2.0], [0.5, 0.3, 0.1], 0.05)
        print(f"[OK] Func.FuncRS.SetUser: ret={r}")
    except Exception as e:
        print(f"[FAIL] Func.FuncRS.SetUser: {e}")

    # --- RS Case ---
    try:
        ret = m.LoadCases.ResponseSpectrum.SetCase('TSX')
        print(f"[OK] RS.SetCase: ret={ret}")
    except Exception as e:
        print(f"[FAIL] RS.SetCase: {e}")

    # --- Diaphragm ---
    try:
        ret = m.Diaphragm.SetDiaphragm('TD', False)
        print(f"[OK] Diaphragm: ret={ret}")
    except Exception as e:
        print(f"[FAIL] Diaphragm: {e}")

    # --- Points ---
    try:
        r = m.PointObj.GetNameList()
        n = r[0] if isinstance(r, (list, tuple)) else 0
        print(f"[OK] PointObj.GetNameList: {n} puntos")
    except Exception as e:
        print(f"[FAIL] PointObj: {e}")

    print("\n=== TEST COMPLETADO ===")
    print("\nSi todo es [OK]: python run_all.py")
    print("Si hay [FAIL]: pegame la salida completa")


if __name__ == '__main__':
    test()
