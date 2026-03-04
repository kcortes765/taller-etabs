"""
07_diaphragm_supports.py — Diafragma rigido en losas + empotramiento en base.
"""
from config_helper import get_model, set_units_tonf_m
from config import LOSA_NAME


def define_diaphragm(m):
    set_units_tonf_m(m)

    # Definir diafragma rigido (SemiRigid=False → rigido)
    ret = m.Diaphragm.SetDiaphragm('DR', False)
    print(f"  Diaphragm 'DR': ret={ret}")

    # Asignar a todas las losas
    result = m.AreaObj.GetNameList()
    if isinstance(result, (list, tuple)):
        area_names = result[1] if len(result) > 1 else []
    else:
        area_names = []

    count = 0
    for area_name in area_names:
        try:
            prop_result = m.AreaObj.GetProperty(area_name)
            prop_name = str(prop_result[0]) if isinstance(prop_result, (list, tuple)) else str(prop_result)
        except:
            continue

        if LOSA_NAME in prop_name:
            try:
                ret = m.AreaObj.SetDiaphragm(area_name, 'DR')
                if ret == 0:
                    count += 1
            except:
                pass

    print(f"[OK] Diafragma rigido asignado a {count} losas")


def assign_base_supports(m):
    set_units_tonf_m(m)

    result = m.PointObj.GetNameList()
    if isinstance(result, (list, tuple)):
        point_names = result[1] if len(result) > 1 else []
    else:
        point_names = []

    count = 0
    for pt in point_names:
        try:
            coord = m.PointObj.GetCoordCartesian(pt)
            if isinstance(coord, (list, tuple)):
                z = coord[2] if len(coord) > 2 else -1
            else:
                continue

            if abs(z) < 0.01:  # Base (z=0)
                ret = m.PointObj.SetRestraint(pt, [True]*6)
                if ret == 0:
                    count += 1
        except:
            pass

    print(f"[OK] {count} puntos empotrados en la base")


def main():
    m = get_model()
    print("\n--- Diafragma rigido ---")
    define_diaphragm(m)
    print("\n--- Empotramientos base ---")
    assign_base_supports(m)
    print("\n=== 07_diaphragm_supports COMPLETADO ===")


if __name__ == '__main__':
    main()
