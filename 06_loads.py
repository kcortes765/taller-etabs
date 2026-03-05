"""
06_loads.py — Definir patrones de carga y asignar cargas a losas.

FIX v3: Mejor manejo de formatos COM, verificacion de cargas asignadas.
"""
from config_helper import get_model, set_units_tonf_m
from config import (
    SCP_OFICINA, SCT_TECHO, TERP_PISO, TERT_TECHO,
    STORY_ELEVATIONS, LOSA_NAME,
)


def define_load_patterns(m):
    set_units_tonf_m(m)

    # eLoadPatternType: 1=Dead, 2=SuperDead, 3=Live, 5=Quake, 11=RoofLive
    patterns = [
        ('PP',   1,  1.0),   # Dead con selfweight
        ('SCP',  3,  0.0),   # Live
        ('SCT',  11, 0.0),   # Roof Live
        ('TERP', 2,  0.0),   # Super Dead
        ('TERT', 2,  0.0),   # Super Dead
        ('SEx',  5,  0.0),   # Quake
        ('SEy',  5,  0.0),   # Quake
    ]

    for name, ltype, sw in patterns:
        try:
            ret = m.LoadPatterns.Add(name, ltype, sw, True)
            status = 'OK' if ret == 0 else f'ret={ret}'
            print(f"  {name}: {status}")
        except Exception as e:
            print(f"  {name}: {e}")

    print("[OK] 7 patrones de carga definidos")


def _extract_z(coord_result):
    """Extraer Z de resultado COM GetCoordCartesian."""
    if coord_result is None:
        return None
    if isinstance(coord_result, (int, float)):
        return None

    vals = list(coord_result) if isinstance(coord_result, tuple) else coord_result

    if len(vals) == 4:
        # (x, y, z, ret) o (ret, x, y, z)
        if isinstance(vals[3], int) or (isinstance(vals[3], float) and vals[3] == 0.0):
            return float(vals[2])
        if isinstance(vals[0], int) and vals[0] == 0:
            return float(vals[3])
        return float(vals[2])

    if len(vals) >= 3:
        return float(vals[2])

    return None


def assign_loads(m):
    """Asignar cargas uniformes a losas segun piso tipo o techo."""
    set_units_tonf_m(m)

    result = m.AreaObj.GetNameList()
    if isinstance(result, (list, tuple)):
        n_areas = result[0] if isinstance(result[0], int) else 0
        area_names = result[1] if len(result) > 1 else []
    else:
        print("[ERROR] No se pudieron obtener areas")
        return

    print(f"  Total areas: {n_areas}")
    if n_areas == 0:
        print("  [WARN] No hay areas — verificar que pasos 3-5 crearon geometria")
        return

    # Cargas en tonf/m2
    scp_tonf  = SCP_OFICINA / 1000.0
    sct_tonf  = SCT_TECHO / 1000.0
    terp_tonf = TERP_PISO / 1000.0
    tert_tonf = TERT_TECHO / 1000.0

    z_techo = STORY_ELEVATIONS[-1]
    count_piso = 0
    count_techo = 0

    for area_name in area_names:
        # Solo asignar a losas, no muros
        try:
            prop_result = m.AreaObj.GetProperty(area_name)
            if isinstance(prop_result, (list, tuple)):
                prop_name = str(prop_result[0])
            else:
                prop_name = str(prop_result)
        except Exception:
            continue

        if LOSA_NAME not in prop_name:
            continue

        # Z de la losa para distinguir techo vs piso tipo
        try:
            pts_result = m.AreaObj.GetPoints(area_name)
            if isinstance(pts_result, (list, tuple)):
                n_pts = pts_result[0] if isinstance(pts_result[0], int) else 0
                pt_names = pts_result[1] if n_pts > 0 else []
            else:
                continue

            if not pt_names:
                continue

            coord_result = m.PointObj.GetCoordCartesian(pt_names[0])
            z = _extract_z(coord_result)
            if z is None:
                z = 0
        except Exception:
            continue

        is_techo = abs(z - z_techo) < 0.1

        try:
            if is_techo:
                m.AreaObj.SetLoadUniform(area_name, 'SCT',  -sct_tonf,  6, True, 'Global')
                m.AreaObj.SetLoadUniform(area_name, 'TERT', -tert_tonf, 6, True, 'Global')
                count_techo += 1
            else:
                m.AreaObj.SetLoadUniform(area_name, 'SCP',  -scp_tonf,  6, True, 'Global')
                m.AreaObj.SetLoadUniform(area_name, 'TERP', -terp_tonf, 6, True, 'Global')
                count_piso += 1
        except Exception as e:
            print(f"  [WARN] Carga en {area_name}: {e}")

    print(f"[OK] Cargas asignadas: {count_piso} losas piso + {count_techo} losas techo")


def main():
    m = get_model()
    print("\n--- Patrones de carga ---")
    define_load_patterns(m)
    print("\n--- Asignando cargas ---")
    assign_loads(m)
    print("\n=== 06_loads COMPLETADO ===")


if __name__ == '__main__':
    main()
