"""
08_spectrum_cases.py — Espectro NCh433+DS61, caso modal, response spectrum,
fuente de masa, combinaciones NCh3171.

FIX v2: Multiples fallbacks para cada API call.
- FuncRS.SetUser: probar con y sin damping arg, probar Func.FuncRS vs directo
- Mass source: 3+ metodos
- Modal: probar ModalEigen y fallback a ModalRitz
- SetModalComb / SetDampConstant: firma alternativa
"""
from config_helper import get_model, set_units_tonf_m
from config import (
    AO_G, I_FACTOR, RO_MUROS, G_ACCEL,
    S_SUELO, TO_SUELO, T_PRIME, N_SUELO, P_SUELO,
)


def build_elastic_spectrum():
    """Espectro elastico NCh433+DS61: Sa/g vs T.
    alpha(T) = (1 + 4.5*(To/T)^p) / (1 + (To/T)^3)
    Sa = S * Ao * alpha  [en fraccion de g]
    """
    T_vals = []
    Sa_vals = []
    dt = 0.05  # cada 0.05s como pide el enunciado

    T = dt  # empezar en 0.05, no en 0
    while T <= 5.01:
        ratio = TO_SUELO / T
        alpha = (1.0 + 4.5 * ratio**P_SUELO) / (1.0 + ratio**3)
        Sa_g = S_SUELO * AO_G * alpha
        T_vals.append(round(T, 4))
        Sa_vals.append(round(Sa_g, 6))
        T += dt

    # Agregar T=0 al inicio (Sa = S*Ao = PGA amplificado)
    T_vals.insert(0, 0.0)
    Sa_vals.insert(0, round(S_SUELO * AO_G, 6))

    return T_vals, Sa_vals


def define_spectrum(m):
    """Definir funcion de espectro en ETABS. Prueba multiples APIs."""
    set_units_tonf_m(m)
    T_vals, Sa_vals = build_elastic_spectrum()
    n = len(T_vals)
    name = 'Espectro_NCh433'
    damp = 0.05

    # Lista de intentos: (descripcion, funcion)
    attempts = []

    # 1. Func.FuncRS.SetUser con 5 args (name, count, T, Sa, damp)
    def try_funcrs_5():
        return m.Func.FuncRS.SetUser(name, n, T_vals, Sa_vals, damp)
    attempts.append(('Func.FuncRS.SetUser(5 args)', try_funcrs_5))

    # 2. Func.FuncRS.SetUser con 4 args (name, count, T, Sa) — sin damping
    def try_funcrs_4():
        return m.Func.FuncRS.SetUser(name, n, T_vals, Sa_vals)
    attempts.append(('Func.FuncRS.SetUser(4 args)', try_funcrs_4))

    # 3. Func.FuncRS.SetUser con solo (name, T, Sa, damp)
    def try_funcrs_no_count():
        return m.Func.FuncRS.SetUser(name, T_vals, Sa_vals, damp)
    attempts.append(('Func.FuncRS.SetUser(no count)', try_funcrs_no_count))

    # 4. Via Func accedido como dict/attribute
    def try_func_direct():
        rs = getattr(m.Func, 'FuncRS', None) or getattr(m.Func, 'ResponseSpectrum', None)
        if rs is None:
            raise AttributeError("Ni FuncRS ni ResponseSpectrum disponible en m.Func")
        return rs.SetUser(name, n, T_vals, Sa_vals, damp)
    attempts.append(('m.Func.[FuncRS|ResponseSpectrum].SetUser', try_func_direct))

    # 5. Intentar definir como archivo de texto y cargar desde archivo
    def try_from_file():
        import os, tempfile
        # Crear archivo de espectro temporal
        spec_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'espectro_nch433.txt')
        with open(spec_file, 'w') as f:
            for t, sa in zip(T_vals, Sa_vals):
                f.write(f"{t}\t{sa}\n")
        # Intentar cargar desde archivo
        try:
            ret = m.Func.FuncRS.SetFromFile(name, spec_file, 1, 0, 1, 2, True)
            return ret
        except Exception:
            # Probar con otro path del API
            ret = m.Func.FuncRS.SetFromFile(name, spec_file)
            return ret
    attempts.append(('FuncRS.SetFromFile (espectro.txt)', try_from_file))

    for desc, func in attempts:
        try:
            ret = func()
            # ret puede ser int o tuple; 0 = OK, -99 o tuple con -99 = parcial
            if isinstance(ret, (list, tuple)):
                code = ret[-1] if ret else -1
            else:
                code = ret

            print(f"  {desc}: ret={ret}")
            if code == 0:
                print(f"[OK] Espectro: {n} puntos (T=0 a 5s)")
                return True
            elif code != 0:
                print(f"  [WARN] ret={code}, intentando siguiente metodo...")
        except AttributeError as e:
            print(f"  {desc}: metodo no existe ({e})")
        except Exception as e:
            print(f"  {desc}: fallo ({e})")

    print("  [ERROR] No se pudo definir espectro con ningún metodo")
    print("  >>> DEFINIR MANUALMENTE: Define > Functions > Response Spectrum > User")
    print(f"      Nombre: {name}")
    print(f"      {n} puntos, T=0 a 5s, dT=0.05s")
    print(f"      Formula: Sa = {S_SUELO}*{AO_G} * alpha(T)")

    # Guardar archivo de espectro para importar manualmente
    import os
    spec_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'espectro_nch433.txt')
    with open(spec_file, 'w') as f:
        for t, sa in zip(T_vals, Sa_vals):
            f.write(f"{t}\t{sa}\n")
    print(f"      Archivo guardado: {spec_file}")
    return False


def define_mass_source(m):
    """Fuente de masa: selfweight + 100%TERP + 25%SCP.

    Prueba multiples APIs segun version ETABS.
    """
    methods = [
        # (nombre, funcion)
        ('PropMass.SetMassSource_1',
         lambda: m.PropMass.SetMassSource_1(
             True, False, True, 2, ['TERP', 'SCP'], [1.0, 0.25])),
        ('MassSource.SetMassSource_1',
         lambda: m.MassSource.SetMassSource_1(
             True, False, True, 2, ['TERP', 'SCP'], [1.0, 0.25])),
        ('PropMaterial.SetMassSource_1',
         lambda: m.PropMaterial.SetMassSource_1(
             True, False, True, 2, ['TERP', 'SCP'], [1.0, 0.25])),
        # Sin el 3er bool (isFromLoads=True)
        ('PropMass.SetMassSource_1 (4 args)',
         lambda: m.PropMass.SetMassSource_1(
             True, False, 2, ['TERP', 'SCP'], [1.0, 0.25])),
        # Con nombre de mass source
        ('MassSource.SetMassSource (named)',
         lambda: m.MassSource.SetMassSource(
             'MsSrc1', True, False, True, 2, ['TERP', 'SCP'], [1.0, 0.25])),
    ]

    for name, func in methods:
        try:
            ret = func()
            print(f"  {name}: ret={ret}")
            if isinstance(ret, int) and ret == 0:
                print("[OK] Fuente de masa sismica definida")
                return True
            elif isinstance(ret, (list, tuple)) and (ret[-1] == 0 or ret[0] == 0):
                print("[OK] Fuente de masa sismica definida")
                return True
        except AttributeError:
            pass  # metodo no existe
        except Exception:
            pass

    print("  [WARN] Mass source no se pudo definir via API")
    print("  >>> DEFINIR MANUALMENTE: Define > Mass Source")
    print("      - Include Element Self Mass: SI")
    print("      - TERP: factor 1.0")
    print("      - SCP:  factor 0.25")
    return False


def define_modal_case(m):
    """Caso modal Eigen con suficientes modos."""
    n_modes = 60  # suficiente para edificio 20 pisos

    # Intentar multiples formas de crear caso modal
    methods = [
        ('ModalEigen.SetCase',
         lambda: m.LoadCases.ModalEigen.SetCase('Modal')),
        ('Modal.SetCase',
         lambda: m.LoadCases.Modal.SetCase('Modal')),
    ]

    case_ok = False
    for desc, func in methods:
        try:
            ret = func()
            print(f"  {desc}: ret={ret}")
            case_ok = True
            break
        except AttributeError:
            print(f"  {desc}: metodo no existe")
        except Exception as e:
            print(f"  {desc}: {e}")

    if not case_ok:
        print("  [WARN] No se pudo crear caso modal via API")
        print("  >>> ETABS crea caso 'MODAL' por defecto al hacer NewBlank")

    # Setear numero de modos
    mode_methods = [
        ('ModalEigen.SetNumberModes(3 args)',
         lambda: m.LoadCases.ModalEigen.SetNumberModes('Modal', n_modes, 1)),
        ('ModalEigen.SetNumberModes(2 args)',
         lambda: m.LoadCases.ModalEigen.SetNumberModes('Modal', n_modes)),
        ('Modal.SetNumberModes',
         lambda: m.LoadCases.Modal.SetNumberModes('Modal', n_modes, 1)),
    ]

    for desc, func in mode_methods:
        try:
            ret = func()
            print(f"  {desc}: ret={ret}")
            break
        except AttributeError:
            pass
        except Exception as e:
            print(f"  {desc}: {e}")

    print(f"[OK] Caso modal: {n_modes} modos (o default ETABS)")


def define_rs_cases(m):
    """Casos Response Spectrum (SEx, SEy)."""
    set_units_tonf_m(m)

    # Factor escala: g = 9.81 (convierte Sa/g a m/s2)
    # Nota: R* se ajusta despues de conocer T* (tras primer analisis)
    sf = G_ACCEL  # 9.81 m/s2

    for case_name, direction in [('SEx', 'U1'), ('SEy', 'U2')]:
        # Crear caso RS
        try:
            ret = m.LoadCases.ResponseSpectrum.SetCase(case_name)
            print(f"  SetCase '{case_name}': ret={ret}")
        except Exception as e:
            print(f"  [ERROR] SetCase {case_name}: {e}")
            continue

        # Vincular al caso modal
        try:
            ret = m.LoadCases.ResponseSpectrum.SetModalCase(case_name, 'Modal')
            print(f"  SetModalCase '{case_name}': ret={ret}")
        except Exception as e:
            # Probar con 'MODAL' (nombre por defecto ETABS)
            try:
                ret = m.LoadCases.ResponseSpectrum.SetModalCase(case_name, 'MODAL')
                print(f"  SetModalCase '{case_name}' (MODAL): ret={ret}")
            except Exception:
                print(f"  [WARN] SetModalCase {case_name}: {e}")

        # Asignar espectro y direccion
        try:
            ret = m.LoadCases.ResponseSpectrum.SetLoads(
                case_name, 1, [direction], ['Espectro_NCh433'],
                [sf], [''], [0.0],
            )
            print(f"  SetLoads '{case_name}': ret={ret}")
        except Exception as e:
            # Probar con menos args
            try:
                ret = m.LoadCases.ResponseSpectrum.SetLoads(
                    case_name, 1, [direction], ['Espectro_NCh433'], [sf],
                )
                print(f"  SetLoads '{case_name}' (5 args): ret={ret}")
            except Exception as e2:
                print(f"  [ERROR] SetLoads {case_name}: {e2}")

        # CQC — probar varias firmas
        for cqc_args in [(case_name, 1, 0.0, 0.0), (case_name, 1)]:
            try:
                ret = m.LoadCases.ResponseSpectrum.SetModalComb(*cqc_args)
                print(f"  SetModalComb CQC ({len(cqc_args)} args): ret={ret}")
                break
            except AttributeError:
                pass
            except Exception:
                pass

        # Damping 5% — probar varias firmas
        for damp_args in [(case_name, 0.05), (case_name, 0, 0.05)]:
            try:
                ret = m.LoadCases.ResponseSpectrum.SetDampConstant(*damp_args)
                print(f"  SetDampConstant 5% ({len(damp_args)} args): ret={ret}")
                break
            except AttributeError:
                pass
            except Exception:
                pass

    print("[OK] Casos RS definidos (SEx, SEy) — espectro elastico, ajustar R* despues")


def define_combinations(m):
    """Combinaciones NCh3171 para diseno."""
    set_units_tonf_m(m)

    combos = {
        'C1_1.4D':       [('PP', 1.4), ('TERP', 1.4), ('TERT', 1.4)],
        'C2_1.2D+1.6L':  [('PP', 1.2), ('TERP', 1.2), ('TERT', 1.2),
                           ('SCP', 1.6), ('SCT', 0.5)],
        'C3_1.2D+L+SEx': [('PP', 1.2), ('TERP', 1.2), ('SCP', 1.0), ('SEx', 1.4)],
        'C4_1.2D+L+SEy': [('PP', 1.2), ('TERP', 1.2), ('SCP', 1.0), ('SEy', 1.4)],
        'C5_0.9D+SEx':   [('PP', 0.9), ('TERP', 0.9), ('SEx', 1.4)],
        'C6_0.9D+SEy':   [('PP', 0.9), ('TERP', 0.9), ('SEy', 1.4)],
        'C7_0.9D-SEx':   [('PP', 0.9), ('TERP', 0.9), ('SEx', -1.4)],
        'C8_0.9D-SEy':   [('PP', 0.9), ('TERP', 0.9), ('SEy', -1.4)],
    }

    ok = 0
    for combo_name, loads in combos.items():
        try:
            ret = m.RespCombo.Add(combo_name, 0)  # 0 = Linear Add
            for pat, sf in loads:
                m.RespCombo.SetCaseList(combo_name, 0, pat, sf)
            ok += 1
        except Exception as e:
            print(f"  [WARN] Combo {combo_name}: {e}")

    print(f"[OK] {ok}/{len(combos)} combinaciones NCh3171 definidas")


def main():
    m = get_model()

    # Cada seccion es independiente — si una falla no pierde las otras
    spectrum_ok = False
    sections = [
        ("Espectro NCh433", lambda: define_spectrum(m)),
        ("Fuente de masa", lambda: define_mass_source(m)),
        ("Caso modal", lambda: define_modal_case(m)),
    ]

    for name, func in sections:
        print(f"\n--- {name} ---")
        try:
            result = func()
            if name == "Espectro NCh433":
                spectrum_ok = result
        except Exception as e:
            print(f"  [ERROR] {name} fallo: {e}")

    print("\n--- Response Spectrum ---")
    if spectrum_ok:
        try:
            define_rs_cases(m)
        except Exception as e:
            print(f"  [ERROR] RS cases fallo: {e}")
    else:
        print("  [SKIP] No se crean RS cases porque el espectro no se definio")
        print("  >>> 1. Definir espectro manualmente en ETABS")
        print("  >>> 2. Re-ejecutar: python 08_spectrum_cases.py")

    print("\n--- Combinaciones ---")
    try:
        define_combinations(m)
    except Exception as e:
        print(f"  [ERROR] Combinaciones fallo: {e}")
        print("  >>> Si ETABS se cerro, abrir Edificio1.edb y definir manualmente")

    print("\n=== 08_spectrum_cases COMPLETADO ===")


if __name__ == '__main__':
    main()
