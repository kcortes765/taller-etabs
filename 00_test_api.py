"""
00_test_api.py — Diagnostico: conectar a ETABS abierto y verificar metodos.
"""
import comtypes.client
import sys


def connect():
    """Conectar al ETABS que esta corriendo."""
    # Metodo 1: GetActiveObject (conecta al ETABS abierto)
    try:
        obj = comtypes.client.GetActiveObject('CSI.ETABS.API.ETABSObject')
        m = obj.SapModel
        m.GetPresentUnits()  # test rapido
        print("[OK] Conectado via GetActiveObject")
        return m
    except Exception as e:
        print(f"  GetActiveObject: {e}")

    # Metodo 2: Helper
    try:
        helper = comtypes.client.CreateObject('ETABSv1.Helper')
        obj = helper.CreateObjectProgID('CSI.ETABS.API.ETABSObject')
        m = obj.SapModel
        m.GetPresentUnits()
        print("[OK] Conectado via Helper")
        return m
    except Exception as e:
        print(f"  Helper: {e}")

    # Metodo 3: CreateObject directo
    try:
        obj = comtypes.client.CreateObject('CSI.ETABS.API.ETABSObject')
        m = obj.SapModel
        m.GetPresentUnits()
        print("[OK] Conectado via CreateObject")
        return m
    except Exception as e:
        print(f"  CreateObject: {e}")

    print("[FAIL] No se pudo conectar a ETABS")
    return None


def test():
    print("=== TEST API ETABS ===\n")

    m = connect()
    if m is None:
        sys.exit(1)

    # Unidades
    try:
        u = m.GetPresentUnits()
        m.SetPresentUnits(9)  # tonf_m_C
        print(f"[OK] Unidades: {u} -> 9 (tonf_m_C)")
    except Exception as e:
        print(f"[FAIL] Unidades: {e}")

    # InitializeNewModel
    try:
        ret = m.InitializeNewModel(9)
        print(f"[OK] InitializeNewModel: ret={ret}")
    except Exception as e:
        print(f"[WARN] InitializeNewModel: {e}")

    # NewBlank
    try:
        ret = m.File.NewBlank()
        print(f"[OK] File.NewBlank: ret={ret}")
    except Exception as e:
        print(f"[WARN] File.NewBlank: {e}")

    # SetStories
    try:
        ret = m.Story.SetStories(
            ['T1', 'T2'], [0.0, 3.0, 6.0], [3.0, 3.0],
            [True, True], ['', ''], [False, False], [0.0, 0.0])
        print(f"[OK] Story.SetStories: ret={ret}")
    except Exception as e:
        print(f"[FAIL] Story.SetStories: {e}")

    # Material
    try:
        ret = m.PropMaterial.SetMaterial('TM', 2)
        print(f"[OK] PropMaterial.SetMaterial: ret={ret}")
    except Exception as e:
        print(f"[FAIL] PropMaterial.SetMaterial: {e}")

    # SetWall (5 params)
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

    # SetSlab
    try:
        ret = m.PropArea.SetSlab('TS', 0, 1, 'TM', 0.15)
        print(f"[OK] PropArea.SetSlab: ret={ret}")
    except Exception as e:
        print(f"[FAIL] PropArea.SetSlab: {e}")

    # SetRectangle
    try:
        ret = m.PropFrame.SetRectangle('TF', 'TM', 0.60, 0.20)
        print(f"[OK] PropFrame.SetRectangle: ret={ret}")
    except Exception as e:
        print(f"[FAIL] PropFrame.SetRectangle: {e}")

    # AreaObj.AddByCoord
    try:
        r = m.AreaObj.AddByCoord(4, [0,1,1,0], [0,0,0,0], [0,0,3,3], '', 'TW', '', 'Global')
        print(f"[OK] AreaObj.AddByCoord: {r}")
    except Exception as e:
        print(f"[FAIL] AreaObj.AddByCoord: {e}")

    # FrameObj.AddByCoord
    try:
        r = m.FrameObj.AddByCoord(0,0,3, 1,0,3, '', 'TF', '', 'Global')
        print(f"[OK] FrameObj.AddByCoord: {r}")
    except Exception as e:
        print(f"[FAIL] FrameObj.AddByCoord: {e}")

    # LoadPatterns
    try:
        ret = m.LoadPatterns.Add('TL', 1, 0, True)
        print(f"[OK] LoadPatterns.Add: ret={ret}")
    except Exception as e:
        print(f"[FAIL] LoadPatterns.Add: {e}")

    # FuncRS
    try:
        r = m.Func.FuncRS.SetUser('TRS', 3, [0.0,1.0,2.0], [0.5,0.3,0.1], 0.05)
        print(f"[OK] Func.FuncRS.SetUser: {r}")
    except Exception as e:
        print(f"[FAIL] Func.FuncRS.SetUser: {e}")

    # RS SetCase
    try:
        ret = m.LoadCases.ResponseSpectrum.SetCase('TSX')
        print(f"[OK] RS.SetCase: ret={ret}")
    except Exception as e:
        print(f"[FAIL] RS.SetCase: {e}")

    # Diaphragm
    try:
        ret = m.Diaphragm.SetDiaphragm('TD', False)
        print(f"[OK] Diaphragm: ret={ret}")
    except Exception as e:
        print(f"[FAIL] Diaphragm: {e}")

    # Restraint
    try:
        r = m.PointObj.GetNameList()
        n = r[0] if isinstance(r, (list,tuple)) else 0
        print(f"[OK] PointObj.GetNameList: {n} puntos")
        if n > 0:
            pt = r[1][0]
            ret = m.PointObj.SetRestraint(pt, [True]*6)
            print(f"[OK] SetRestraint: ret={ret}")
    except Exception as e:
        print(f"[FAIL] PointObj: {e}")

    print("\n=== TEST COMPLETADO ===")


if __name__ == '__main__':
    test()
