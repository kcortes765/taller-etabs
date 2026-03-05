"""
07_diaphragm_supports.py — Diafragma rigido en losas + empotramiento en base.

FIX: empotramientos ahora usa GetCoordCartesian con manejo robusto del formato
COM (puede retornar tuple de floats o tuple con ret code al final).
"""
from config_helper import get_model, set_units_tonf_m
from config import LOSA_NAME


def define_diaphragm(m):
    """Asignar diafragma rigido a todas las losas."""
    set_units_tonf_m(m)

    # Intentar crear diafragma explicito 'DR'
    diaph_name = None
    if m.Diaphragm is not None:
        try:
            ret = m.Diaphragm.SetDiaphragm('DR', False)
            if ret == 0:
                diaph_name = 'DR'
                print(f"  Diaphragm.SetDiaphragm 'DR': ret={ret}")
        except Exception as e:
            print(f"  Diaphragm.SetDiaphragm fallo: {e}")

    if diaph_name is None:
        diaph_name = 'D1'  # default en v19 tras NewBlank
        print(f"  Usando diafragma por defecto '{diaph_name}'")

    # Obtener todas las areas
    result = m.AreaObj.GetNameList()
    if isinstance(result, (list, tuple)) and len(result) > 1:
        area_names = result[1] if result[1] is not None else []
    else:
        area_names = []

    count = 0
    for area_name in area_names:
        # Verificar si es losa
        try:
            prop_result = m.AreaObj.GetProperty(area_name)
            prop_name = str(prop_result[0]) if isinstance(prop_result, (list, tuple)) else str(prop_result)
        except Exception:
            continue

        if LOSA_NAME not in prop_name:
            continue

        # Asignar diafragma
        for dname in [diaph_name, 'DR', 'D1']:
            try:
                ret = m.AreaObj.SetDiaphragm(area_name, dname)
                if ret == 0:
                    count += 1
                    break
            except Exception:
                continue

    print(f"[OK] Diafragma rigido asignado a {count} losas")
    return diaph_name


def assign_base_supports(m):
    """Empotrar todos los puntos en z=0 (base).

    FIX: GetCoordCartesian retorna distintos formatos segun version:
    - v19 Helper.CreateObject: (x, y, z, ret) o (x, y, z)
    - v19 GetActiveObject: puede retornar (ret, x, y, z)
    Se prueba ambos formatos.
    """
    set_units_tonf_m(m)

    result = m.PointObj.GetNameList()
    if isinstance(result, (list, tuple)) and len(result) > 1:
        point_names = result[1] if result[1] is not None else []
    else:
        point_names = []

    total = len(point_names) if hasattr(point_names, '__len__') else 0
    print(f"  Total puntos en modelo: {total}")

    if total == 0:
        print("  [WARN] No hay puntos en el modelo!")
        return

    # Diagnostico: probar con el primer punto para entender el formato
    sample_pt = point_names[0]
    try:
        coord = m.PointObj.GetCoordCartesian(sample_pt)
        print(f"  [DEBUG] GetCoordCartesian('{sample_pt}') = {coord}")
    except Exception as e:
        print(f"  [ERROR] GetCoordCartesian fallo: {e}")
        # Fallback: intentar con (x,y,z) como output params
        try:
            coord = m.PointObj.GetCoordCartesian(sample_pt, 0.0, 0.0, 0.0)
            print(f"  [DEBUG] GetCoordCartesian(4 args) = {coord}")
        except Exception as e2:
            print(f"  [ERROR] GetCoordCartesian(4 args) fallo: {e2}")
            return

    def extract_z(coord_result):
        """Extraer Z de resultado COM. Intenta varios formatos."""
        if coord_result is None:
            return None
        if isinstance(coord_result, (int, float)):
            return None  # Solo retorno un numero, no coords

        vals = list(coord_result) if isinstance(coord_result, tuple) else coord_result

        # Formato (x, y, z, ret) — 4 elementos, z es indice 2
        if len(vals) == 4:
            # Si el ultimo valor es 0 (ret=OK), z es indice 2
            if isinstance(vals[3], int) or (isinstance(vals[3], float) and vals[3] == 0.0):
                return float(vals[2])
            # Si el primer valor es 0 (ret=OK), z es indice 3
            if isinstance(vals[0], int) and vals[0] == 0:
                return float(vals[3])
            # Asumir (x, y, z, ret)
            return float(vals[2])

        # Formato (x, y, z) — 3 elementos
        if len(vals) >= 3:
            return float(vals[2])

        return None

    count = 0
    errors = 0
    for pt in point_names:
        try:
            coord = m.PointObj.GetCoordCartesian(pt)
            z = extract_z(coord)

            if z is not None and abs(z) < 0.01:
                ret = m.PointObj.SetRestraint(pt, [True] * 6)
                if ret == 0:
                    count += 1
        except Exception:
            errors += 1

    if count == 0 and total > 0:
        # Fallback: probar con 4 argumentos
        print("  Metodo 1 no encontro puntos en z=0. Probando con 4 args...")
        for pt in point_names:
            try:
                coord = m.PointObj.GetCoordCartesian(pt, 0.0, 0.0, 0.0)
                z = extract_z(coord)
                if z is not None and abs(z) < 0.01:
                    ret = m.PointObj.SetRestraint(pt, [True] * 6)
                    if ret == 0:
                        count += 1
            except Exception:
                pass

    if count == 0 and total > 0:
        # Ultimo fallback: asignar restriccion a TODOS los puntos que esten
        # en la elevacion minima del modelo
        print("  Fallback: buscando elevacion minima...")
        z_vals = []
        for pt in list(point_names)[:50]:  # muestra de 50
            try:
                coord = m.PointObj.GetCoordCartesian(pt)
                z = extract_z(coord)
                if z is not None:
                    z_vals.append(z)
            except Exception:
                pass

        if z_vals:
            z_min = min(z_vals)
            print(f"  Z minima encontrada: {z_min:.3f} m")
            for pt in point_names:
                try:
                    coord = m.PointObj.GetCoordCartesian(pt)
                    z = extract_z(coord)
                    if z is not None and abs(z - z_min) < 0.01:
                        ret = m.PointObj.SetRestraint(pt, [True] * 6)
                        if ret == 0:
                            count += 1
                except Exception:
                    pass

    print(f"[OK] {count} puntos empotrados en la base")
    if errors > 0:
        print(f"  [WARN] {errors} errores en GetCoordCartesian")


def remove_all_diaphragms(m):
    """Quitar diafragma rigido de todas las losas. Para modelo semi-rigido."""
    set_units_tonf_m(m)

    result = m.AreaObj.GetNameList()
    if isinstance(result, (list, tuple)) and len(result) > 1:
        area_names = result[1] if result[1] is not None else []
    else:
        return 0

    count = 0
    for area_name in area_names:
        try:
            prop_result = m.AreaObj.GetProperty(area_name)
            prop_name = str(prop_result[0]) if isinstance(prop_result, (list, tuple)) else str(prop_result)
        except Exception:
            continue

        if LOSA_NAME not in prop_name:
            continue

        # Intentar varias formas de quitar diafragma
        for dname in ['None', '', None]:
            try:
                ret = m.AreaObj.SetDiaphragm(area_name, dname)
                if ret == 0:
                    count += 1
                    break
            except Exception:
                continue

    print(f"  Diafragma removido de {count} losas")
    return count


def main():
    m = get_model()
    print("\n--- Diafragma rigido ---")
    define_diaphragm(m)
    print("\n--- Empotramientos base ---")
    assign_base_supports(m)
    print("\n=== 07_diaphragm_supports COMPLETADO ===")


if __name__ == '__main__':
    main()
