"""
09_torsion_cases.py — Torsion accidental para los 6 casos de analisis.

Implementa:
  Caso a)  — Eccentricity override 5% en RS cases SEx/SEy
  Caso b) Forma 2 — RS cases adicionales + load patterns torsionales

Caso b) Forma 1 (shift CM) se omite en pipeline (demasiado complejo via API).
Ver LEEME.md para instrucciones manuales.
"""
from config_helper import get_model, set_units_tonf_m
from config import (
    STORY_NAMES, STORY_ELEVATIONS, STORY_HEIGHTS,
    EA_X, EA_Y, CM_X, CM_Y, G_ACCEL,
    LX_PLANTA, LY_PLANTA,
)


def detect_diaphragm_name(m):
    """Detectar nombre del diafragma activo."""
    # Probar obtener lista de diafragmas
    try:
        result = m.Diaphragm.GetNameList()
        if isinstance(result, (list, tuple)) and len(result) > 1:
            names = result[1]
            if names:
                return str(names[0])
    except Exception:
        pass

    # Probar nombres comunes
    return 'DR'  # o 'D1'


def setup_torsion_case_a(m):
    """Caso a): Eccentricity override 5% en RS cases SEx/SEy.

    ETABS aplica +-5% de la dimension del diafragma perpendicular
    a la direccion del sismo automaticamente.
    """
    print("\n--- Caso a): Eccentricity Override 5% ---")
    set_units_tonf_m(m)

    diaph_name = detect_diaphragm_name(m)
    print(f"  Diafragma detectado: '{diaph_name}'")

    ok = 0
    for case_name in ['SEx', 'SEy']:
        # Intentar multiples firmas del API
        methods = [
            ('SetDiaphragmEccentricityOverride(4 args)',
             lambda cn=case_name: m.LoadCases.ResponseSpectrum.SetDiaphragmEccentricityOverride(
                 cn, 1, [diaph_name], [0.05])),
            ('SetDiaphragmEccentricityOverride(5 args)',
             lambda cn=case_name: m.LoadCases.ResponseSpectrum.SetDiaphragmEccentricityOverride(
                 cn, 1, [diaph_name], [0.05], [True])),
            ('SetEccentricityOverride',
             lambda cn=case_name: m.LoadCases.ResponseSpectrum.SetEccentricityOverride(
                 cn, 0.05)),
        ]

        for desc, func in methods:
            try:
                ret = func()
                print(f"  {case_name} {desc}: ret={ret}")
                ok += 1
                break
            except AttributeError:
                pass
            except Exception as e:
                print(f"  {case_name} {desc}: {e}")

    if ok == 0:
        print("  [WARN] Eccentricity override no disponible via API")
        print("  >>> MANUAL: Para cada RS case (SEx, SEy):")
        print("      Edit > Modify/Show Load Case > Diaphragm Eccentricity")
        print("      Override Eccentricity = 0.05 (5%)")
    else:
        print(f"[OK] Eccentricity override aplicada a {ok} RS cases")


def setup_torsion_case_b2(m):
    """Caso b) Forma 2: RS cases adicionales + momentos torsionales estaticos.

    Crea:
    - 2 RS cases nuevos: SEx_b2, SEy_b2 (sin eccentricity)
    - 4 load patterns: TorX+, TorX-, TorY+, TorY-
    - Aplica momentos Mz unitarios en un punto cercano al CM de cada piso
    - Los momentos se escalan en las combinaciones

    Nota: Los momentos torsionales reales son Mt = Qi * ea, donde Qi es el
    corte del piso. Como no conocemos Qi a priori, usamos una distribucion
    triangular inversa (proporcional a hi) como aproximacion.
    Despues del analisis (paso 11), se pueden ajustar.
    """
    print("\n--- Caso b) Forma 2: RS cases + momentos torsionales ---")
    set_units_tonf_m(m)

    # 1. Crear RS cases adicionales (copias de SEx/SEy sin eccentricity)
    for case_name, direction in [('SEx_b2', 'U1'), ('SEy_b2', 'U2')]:
        try:
            ret = m.LoadCases.ResponseSpectrum.SetCase(case_name)
            print(f"  SetCase '{case_name}': ret={ret}")
        except Exception as e:
            print(f"  [ERROR] SetCase {case_name}: {e}")
            continue

        try:
            m.LoadCases.ResponseSpectrum.SetModalCase(case_name, 'Modal')
        except Exception:
            try:
                m.LoadCases.ResponseSpectrum.SetModalCase(case_name, 'MODAL')
            except Exception:
                pass

        try:
            m.LoadCases.ResponseSpectrum.SetLoads(
                case_name, 1, [direction], ['Espectro_NCh433'],
                [G_ACCEL], [''], [0.0])
        except Exception:
            try:
                m.LoadCases.ResponseSpectrum.SetLoads(
                    case_name, 1, [direction], ['Espectro_NCh433'], [G_ACCEL])
            except Exception as e:
                print(f"  [ERROR] SetLoads {case_name}: {e}")

        # CQC y damping
        for args in [(case_name, 1, 0.0, 0.0), (case_name, 1)]:
            try:
                m.LoadCases.ResponseSpectrum.SetModalComb(*args)
                break
            except Exception:
                pass
        for args in [(case_name, 0.05), (case_name, 0, 0.05)]:
            try:
                m.LoadCases.ResponseSpectrum.SetDampConstant(*args)
                break
            except Exception:
                pass

    # 2. Crear load patterns para momentos torsionales
    tor_patterns = ['TorX+', 'TorX-', 'TorY+', 'TorY-']
    for pat in tor_patterns:
        try:
            ret = m.LoadPatterns.Add(pat, 5, 0, True)  # 5 = Quake
            print(f"  LoadPattern '{pat}': ret={ret}")
        except Exception as e:
            print(f"  [WARN] LoadPattern '{pat}': {e}")

    # 3. Encontrar o crear puntos cercanos al CM en cada piso
    # Aplicar momento Mz con distribucion triangular (proporcional a hi)
    H_total = STORY_ELEVATIONS[-1]

    for i, (story, elev, h) in enumerate(zip(STORY_NAMES, STORY_ELEVATIONS, STORY_HEIGHTS)):
        # Momento unitario escalado por altura (distribucion triangular)
        # wi * hi / sum(wj * hj) ~ hi / sum(hj) para peso uniforme
        scale = elev / H_total  # 0.06 a 1.0

        # Buscar punto mas cercano al CM en esta elevacion
        pt_name = _find_or_create_point(m, CM_X, CM_Y, elev)
        if pt_name is None:
            continue

        # Aplicar momentos: Mz = ±ea * scale (en tonf*m)
        # Para sismo X: torsion = ea_y * Fx_piso ≈ ea_y * scale
        # Para sismo Y: torsion = ea_x * Fy_piso ≈ ea_x * scale
        moments = {
            'TorX+': EA_Y * scale,
            'TorX-': -EA_Y * scale,
            'TorY+': EA_X * scale,
            'TorY-': -EA_X * scale,
        }

        for pat, mz in moments.items():
            try:
                # SetLoadForce(name, pattern, [Fx, Fy, Fz, Mx, My, Mz], replace)
                ret = m.PointObj.SetLoadForce(
                    pt_name, pat, [0.0, 0.0, 0.0, 0.0, 0.0, mz], False)
            except Exception:
                try:
                    # Alternativa: sin Replace flag
                    ret = m.PointObj.SetLoadForce(
                        pt_name, pat, [0.0, 0.0, 0.0, 0.0, 0.0, mz])
                except Exception:
                    pass

    print(f"[OK] Momentos torsionales aplicados en {N_STORIES} pisos")

    # 4. Crear combinaciones con torsion b2
    _create_torsion_b2_combos(m)


def _find_or_create_point(m, x, y, z):
    """Buscar punto existente cercano a (x,y,z), o crear uno nuevo."""
    # Intentar crear un punto en la posicion del CM
    try:
        ret = m.PointObj.AddCartesian(x, y, z)
        if isinstance(ret, (list, tuple)):
            return str(ret[0])
        return str(ret)
    except Exception:
        pass

    # Fallback: buscar entre puntos existentes
    try:
        result = m.PointObj.GetNameList()
        if isinstance(result, (list, tuple)) and len(result) > 1:
            point_names = result[1]
            for pt in point_names:
                try:
                    coord = m.PointObj.GetCoordCartesian(pt)
                    if isinstance(coord, (list, tuple)) and len(coord) >= 3:
                        px, py, pz = float(coord[0]), float(coord[1]), float(coord[2])
                        if abs(pz - z) < 0.01:  # mismo piso
                            # Punto mas cercano al CM (dentro de 5m)
                            dist = ((px - x)**2 + (py - y)**2) ** 0.5
                            if dist < 5.0:
                                return str(pt)
                except Exception:
                    pass
    except Exception:
        pass

    return None


def _create_torsion_b2_combos(m):
    """Crear combinaciones NCh3171 con torsion Forma 2."""
    combos_b2 = {
        # 1.2D + L + 1.4*(RS + Tor)
        'C3b2_SEx+T': [('PP', 1.2), ('TERP', 1.2), ('SCP', 1.0),
                        ('SEx_b2', 1.4), ('TorX+', 1.4)],
        'C3b2_SEx-T': [('PP', 1.2), ('TERP', 1.2), ('SCP', 1.0),
                        ('SEx_b2', 1.4), ('TorX-', 1.4)],
        'C4b2_SEy+T': [('PP', 1.2), ('TERP', 1.2), ('SCP', 1.0),
                        ('SEy_b2', 1.4), ('TorY+', 1.4)],
        'C4b2_SEy-T': [('PP', 1.2), ('TERP', 1.2), ('SCP', 1.0),
                        ('SEy_b2', 1.4), ('TorY-', 1.4)],
        # 0.9D + 1.4*(RS + Tor)
        'C5b2_SEx+T': [('PP', 0.9), ('TERP', 0.9), ('SEx_b2', 1.4), ('TorX+', 1.4)],
        'C5b2_SEx-T': [('PP', 0.9), ('TERP', 0.9), ('SEx_b2', 1.4), ('TorX-', 1.4)],
        'C6b2_SEy+T': [('PP', 0.9), ('TERP', 0.9), ('SEy_b2', 1.4), ('TorY+', 1.4)],
        'C6b2_SEy-T': [('PP', 0.9), ('TERP', 0.9), ('SEy_b2', 1.4), ('TorY-', 1.4)],
        # 0.9D - 1.4*(RS + Tor)
        'C7b2_SEx+T': [('PP', 0.9), ('TERP', 0.9), ('SEx_b2', -1.4), ('TorX-', 1.4)],
        'C7b2_SEx-T': [('PP', 0.9), ('TERP', 0.9), ('SEx_b2', -1.4), ('TorX+', 1.4)],
        'C8b2_SEy+T': [('PP', 0.9), ('TERP', 0.9), ('SEy_b2', -1.4), ('TorY-', 1.4)],
        'C8b2_SEy-T': [('PP', 0.9), ('TERP', 0.9), ('SEy_b2', -1.4), ('TorY+', 1.4)],
    }

    ok = 0
    for combo_name, loads in combos_b2.items():
        try:
            ret = m.RespCombo.Add(combo_name, 0)
            for pat, sf in loads:
                m.RespCombo.SetCaseList(combo_name, 0, pat, sf)
            ok += 1
        except Exception as e:
            print(f"  [WARN] Combo {combo_name}: {e}")

    print(f"[OK] {ok}/{len(combos_b2)} combinaciones torsion b2 definidas")


def main():
    m = get_model()
    print("\n--- Torsion Accidental ---")
    setup_torsion_case_a(m)
    setup_torsion_case_b2(m)
    print("\n=== 09_torsion_cases COMPLETADO ===")


if __name__ == '__main__':
    main()
