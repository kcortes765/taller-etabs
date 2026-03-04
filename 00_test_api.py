"""
00_test_api.py — Diagnostico: verifica que cada metodo de la API ETABS existe.
Correr PRIMERO antes de run_all.py para detectar problemas.
"""
import comtypes.client
import sys


def test():
    print("=== TEST API ETABS ===\n")

    # 1. Conexion
    try:
        obj = comtypes.client.CreateObject('CSI.ETABS.API.ETABSObject')
        m = obj.SapModel
        print("[OK] Conexion a ETABS")
    except Exception as e:
        print(f"[FAIL] Conexion: {e}")
        sys.exit(1)

    # 2. Unidades
    try:
        units = m.GetPresentUnits()
        m.SetPresentUnits(9)  # tonf_m_C
        print(f"[OK] Unidades: {units} -> 9 (tonf_m_C)")
    except Exception as e:
        print(f"[FAIL] Unidades: {e}")

    # 3. InitializeNewModel
    try:
        ret = m.InitializeNewModel(9)
        print(f"[OK] InitializeNewModel: ret={ret}")
    except Exception as e:
        print(f"[WARN] InitializeNewModel: {e}")

    # 4. NewBlank
    try:
        ret = m.File.NewBlank()
        print(f"[OK] File.NewBlank: ret={ret}")
    except Exception as e:
        print(f"[WARN] File.NewBlank: {e}")

    # 5. Story.SetStories
    try:
        ret = m.Story.SetStories(
            ['Test1', 'Test2'],
            [0.0, 3.0, 6.0],
            [3.0, 3.0],
            [True, True],
            ['', ''],
            [False, False],
            [0.0, 0.0],
        )
        print(f"[OK] Story.SetStories: ret={ret}")
    except Exception as e:
        print(f"[FAIL] Story.SetStories: {e}")

    # 6. PropMaterial.SetMaterial
    try:
        ret = m.PropMaterial.SetMaterial('TestMat', 2)
        print(f"[OK] PropMaterial.SetMaterial: ret={ret}")
    except Exception as e:
        print(f"[FAIL] PropMaterial.SetMaterial: {e}")

    # 7. PropArea.SetWall
    try:
        ret = m.PropArea.SetWall('TestWall', 1, 1, 'TestMat', 0.30)
        print(f"[OK] PropArea.SetWall(5 params): ret={ret}")
    except Exception as e:
        print(f"[WARN] SetWall 5 params: {e}")
        try:
            ret = m.PropArea.SetWall('TestWall', 1, 'TestMat', 0.30)
            print(f"[OK] PropArea.SetWall(4 params): ret={ret}")
        except Exception as e2:
            print(f"[FAIL] SetWall 4 params: {e2}")

    # 8. PropArea.SetSlab
    try:
        ret = m.PropArea.SetSlab('TestSlab', 0, 1, 'TestMat', 0.15)
        print(f"[OK] PropArea.SetSlab: ret={ret}")
    except Exception as e:
        print(f"[FAIL] PropArea.SetSlab: {e}")

    # 9. PropFrame.SetRectangle
    try:
        ret = m.PropFrame.SetRectangle('TestFrame', 'TestMat', 0.60, 0.20)
        print(f"[OK] PropFrame.SetRectangle: ret={ret}")
    except Exception as e:
        print(f"[FAIL] PropFrame.SetRectangle: {e}")

    # 10. AreaObj.AddByCoord
    try:
        result = m.AreaObj.AddByCoord(
            4, [0,1,1,0], [0,0,0,0], [0,0,3,3],
            '', 'TestWall', '', 'Global'
        )
        print(f"[OK] AreaObj.AddByCoord: result={result}")
    except Exception as e:
        print(f"[FAIL] AreaObj.AddByCoord: {e}")

    # 11. FrameObj.AddByCoord
    try:
        result = m.FrameObj.AddByCoord(
            0, 0, 3, 1, 0, 3,
            '', 'TestFrame', '', 'Global'
        )
        print(f"[OK] FrameObj.AddByCoord: result={result}")
    except Exception as e:
        print(f"[FAIL] FrameObj.AddByCoord: {e}")

    # 12. LoadPatterns.Add
    try:
        ret = m.LoadPatterns.Add('TestLoad', 1, 0, True)
        print(f"[OK] LoadPatterns.Add: ret={ret}")
    except Exception as e:
        print(f"[FAIL] LoadPatterns.Add: {e}")

    # 13. Func.ResponseSpectrum.SetUser
    try:
        ret = m.Func.ResponseSpectrum.SetUser(
            'TestRS', 3, [0.0, 1.0, 2.0], [0.5, 0.3, 0.1], 0.05
        )
        print(f"[OK] Func.ResponseSpectrum.SetUser: ret={ret}")
    except Exception as e:
        print(f"[WARN] Func.ResponseSpectrum.SetUser: {e}")
        try:
            ret = m.Func.FuncRS.SetUser(
                'TestRS', 3, [0.0, 1.0, 2.0], [0.5, 0.3, 0.1], 0.05
            )
            print(f"[OK] Func.FuncRS.SetUser: ret={ret}")
        except Exception as e2:
            print(f"[FAIL] Ambos metodos RS: {e2}")

    # 14. LoadCases.ResponseSpectrum.SetCase
    try:
        ret = m.LoadCases.ResponseSpectrum.SetCase('TestSEx')
        print(f"[OK] LoadCases.ResponseSpectrum.SetCase: ret={ret}")
    except Exception as e:
        print(f"[FAIL] RS SetCase: {e}")

    # 15. PropMass.SetMassSource_1
    try:
        ret = m.PropMass.SetMassSource_1(
            True, False, True, 1, ['TestLoad'], [1.0]
        )
        print(f"[OK] PropMass.SetMassSource_1: ret={ret}")
    except Exception as e:
        print(f"[WARN] PropMass.SetMassSource_1: {e}")

    # 16. Diaphragm
    try:
        ret = m.Diaphragm.SetDiaphragm('TestD', False)
        print(f"[OK] Diaphragm.SetDiaphragm: ret={ret}")
    except Exception as e:
        print(f"[FAIL] Diaphragm: {e}")

    # 17. PointObj.SetRestraint
    try:
        names = m.PointObj.GetNameList()
        print(f"[OK] PointObj.GetNameList: {names[0]} puntos")
        if names[0] > 0:
            pt = names[1][0]
            ret = m.PointObj.SetRestraint(pt, [True]*6)
            print(f"[OK] PointObj.SetRestraint: ret={ret}")
    except Exception as e:
        print(f"[FAIL] PointObj: {e}")

    print("\n=== TEST COMPLETADO ===")
    print("Copia los resultados y pegamelos para ajustar los scripts.")


if __name__ == '__main__':
    test()
