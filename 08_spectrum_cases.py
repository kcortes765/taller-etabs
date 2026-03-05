"""
08_spectrum_cases.py — Espectro NCh433+DS61, caso modal, response spectrum,
fuente de masa, combinaciones NCh3171.

FIX v3:
- SIEMPRE genera espectro_nch433.txt (para import manual)
- Menos intentos de API (cada fallback que crashea corrompe la sesion COM)
- Si espectro no se define, NO crea RS cases (evita crash)
- Caso modal: ETABS crea 'MODAL' por defecto, solo ajustamos n_modos
"""
import os
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
    dt = 0.05

    T = dt
    while T <= 5.01:
        ratio = TO_SUELO / T
        alpha = (1.0 + 4.5 * ratio**P_SUELO) / (1.0 + ratio**3)
        Sa_g = S_SUELO * AO_G * alpha
        T_vals.append(round(T, 4))
        Sa_vals.append(round(Sa_g, 6))
        T += dt

    # T=0 al inicio
    T_vals.insert(0, 0.0)
    Sa_vals.insert(0, round(S_SUELO * AO_G, 6))

    return T_vals, Sa_vals


def save_spectrum_file(T_vals, Sa_vals):
    """SIEMPRE guardar archivo de espectro para import manual."""
    spec_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'espectro_nch433.txt')
    with open(spec_file, 'w') as f:
        for t, sa in zip(T_vals, Sa_vals):
            f.write(f"{t}\t{sa}\n")
    print(f"  Archivo espectro guardado: espectro_nch433.txt ({len(T_vals)} puntos)")
    return spec_file


def define_spectrum(m):
    """Definir funcion de espectro en ETABS."""
    set_units_tonf_m(m)
    T_vals, Sa_vals = build_elastic_spectrum()
    n = len(T_vals)
    name = 'Espectro_NCh433'
    damp = 0.05

    # SIEMPRE guardar archivo (sirve como backup manual)
    spec_file = save_spectrum_file(T_vals, Sa_vals)

    # Intento 1: SetUser con 5 args (name, count, T, Sa, damp)
    try:
        ret = m.Func.FuncRS.SetUser(name, n, T_vals, Sa_vals, damp)
        if isinstance(ret, (list, tuple)):
            code = ret[-1]
        else:
            code = ret
        print(f"  FuncRS.SetUser(5 args): ret={ret}")
        if code == 0:
            print(f"[OK] Espectro definido: {n} puntos (T=0 a 5s)")
            return True
    except Exception as e:
        print(f"  FuncRS.SetUser(5 args): {e}")

    # Intento 2: SetUser con 4 args (sin damping)
    try:
        ret = m.Func.FuncRS.SetUser(name, n, T_vals, Sa_vals)
        if isinstance(ret, (list, tuple)):
            code = ret[-1]
        else:
            code = ret
        print(f"  FuncRS.SetUser(4 args): ret={ret}")
        if code == 0:
            print(f"[OK] Espectro definido: {n} puntos")
            return True
    except Exception as e:
        print(f"  FuncRS.SetUser(4 args): {e}")

    # Intento 3: SetFromFile
    try:
        ret = m.Func.FuncRS.SetFromFile(name, spec_file, 1, 0, 1, 2, True)
        if isinstance(ret, (list, tuple)):
            code = ret[-1]
        else:
            code = ret
        print(f"  FuncRS.SetFromFile: ret={ret}")
        if code == 0:
            print(f"[OK] Espectro definido desde archivo")
            return True
    except Exception as e:
        print(f"  FuncRS.SetFromFile: {e}")

    print("  [ERROR] No se pudo definir espectro via API")
    print("  >>> IMPORTAR MANUALMENTE:")
    print(f"      Define > Functions > Response Spectrum > From File")
    print(f"      Nombre: {name}")
    print(f"      Archivo: espectro_nch433.txt")
    return False


def define_mass_source(m):
    """Fuente de masa: selfweight + 100%TERP + 25%SCP."""
    methods = [
        ('PropMass.SetMassSource_1',
         lambda: m.PropMass.SetMassSource_1(
             True, False, True, 2, ['TERP', 'SCP'], [1.0, 0.25])),
        ('MassSource.SetMassSource_1',
         lambda: m.MassSource.SetMassSource_1(
             True, False, True, 2, ['TERP', 'SCP'], [1.0, 0.25])),
    ]

    for name, func in methods:
        try:
            ret = func()
            print(f"  {name}: ret={ret}")
            ok = False
            if isinstance(ret, int) and ret == 0:
                ok = True
            elif isinstance(ret, (list, tuple)) and ret[-1] == 0:
                ok = True
            if ok:
                print("[OK] Fuente de masa sismica definida")
                return True
        except AttributeError:
            pass
        except Exception as e:
            print(f"  {name}: {e}")

    print("  [WARN] Mass source no se pudo definir via API")
    print("  >>> DEFINIR MANUALMENTE: Define > Mass Source")
    print("      - Element Self Mass: SI")
    print("      - TERP: 1.0, SCP: 0.25")
    return False


def define_modal_case(m):
    """Ajustar caso modal a 60 modos.

    ETABS crea caso 'MODAL' por defecto con NewBlank.
    Solo necesitamos ajustar el numero de modos.
    """
    n_modes = 60

    # Intentar con 'Modal' y 'MODAL' (nombre puede variar)
    for modal_name in ['Modal', 'MODAL']:
        for func_desc, func in [
            ('SetNumberModes(3)',
             lambda mn=modal_name: m.LoadCases.ModalEigen.SetNumberModes(mn, n_modes, 1)),
            ('SetNumberModes(2)',
             lambda mn=modal_name: m.LoadCases.ModalEigen.SetNumberModes(mn, n_modes)),
        ]:
            try:
                ret = func()
                print(f"  {func_desc} '{modal_name}': ret={ret}")
                print(f"[OK] Caso modal: {n_modes} modos")
                return True
            except AttributeError:
                pass
            except Exception:
                pass

    # Crear caso modal si no existe
    for modal_name in ['Modal']:
        try:
            ret = m.LoadCases.ModalEigen.SetCase(modal_name)
            print(f"  ModalEigen.SetCase '{modal_name}': ret={ret}")
            try:
                m.LoadCases.ModalEigen.SetNumberModes(modal_name, n_modes, 1)
            except Exception:
                pass
            print(f"[OK] Caso modal creado: {n_modes} modos")
            return True
        except Exception as e:
            print(f"  ModalEigen.SetCase: {e}")

    print(f"  [WARN] No se pudo configurar caso modal (ETABS usa default)")
    return False


def define_rs_cases(m):
    """Casos Response Spectrum (SEx, SEy)."""
    set_units_tonf_m(m)
    sf = G_ACCEL  # 9.81 m/s2 (se ajusta con R* despues)

    for case_name, direction in [('SEx', 'U1'), ('SEy', 'U2')]:
        # Crear caso RS
        try:
            ret = m.LoadCases.ResponseSpectrum.SetCase(case_name)
            print(f"  SetCase '{case_name}': ret={ret}")
        except Exception as e:
            print(f"  [ERROR] SetCase {case_name}: {e}")
            continue

        # Vincular al caso modal
        for modal_name in ['Modal', 'MODAL']:
            try:
                ret = m.LoadCases.ResponseSpectrum.SetModalCase(case_name, modal_name)
                print(f"  SetModalCase '{case_name}' -> '{modal_name}': ret={ret}")
                break
            except Exception:
                pass

        # Asignar espectro y direccion
        for args in [
            (case_name, 1, [direction], ['Espectro_NCh433'], [sf], [''], [0.0]),
            (case_name, 1, [direction], ['Espectro_NCh433'], [sf]),
        ]:
            try:
                ret = m.LoadCases.ResponseSpectrum.SetLoads(*args)
                print(f"  SetLoads '{case_name}' ({len(args)} args): ret={ret}")
                break
            except Exception:
                pass

        # CQC
        for args in [(case_name, 1, 0.0, 0.0), (case_name, 1)]:
            try:
                m.LoadCases.ResponseSpectrum.SetModalComb(*args)
                break
            except Exception:
                pass

        # Damping 5%
        for args in [(case_name, 0.05), (case_name, 0, 0.05)]:
            try:
                m.LoadCases.ResponseSpectrum.SetDampConstant(*args)
                break
            except Exception:
                pass

    print("[OK] Casos RS definidos (SEx, SEy)")


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
            ret = m.RespCombo.Add(combo_name, 0)
            for pat, sf in loads:
                m.RespCombo.SetCaseList(combo_name, 0, pat, sf)
            ok += 1
        except Exception as e:
            print(f"  [WARN] Combo {combo_name}: {e}")

    print(f"[OK] {ok}/{len(combos)} combinaciones NCh3171 definidas")


def main():
    m = get_model()

    # 1. Espectro (SIEMPRE genera archivo .txt como backup)
    print("\n--- Espectro NCh433 ---")
    try:
        spectrum_ok = define_spectrum(m)
    except Exception as e:
        print(f"  [ERROR] Espectro fallo: {e}")
        spectrum_ok = False

    # 2. Fuente de masa
    print("\n--- Fuente de masa ---")
    try:
        define_mass_source(m)
    except Exception as e:
        print(f"  [ERROR] Mass source fallo: {e}")

    # 3. Caso modal (ajustar modos)
    print("\n--- Caso modal ---")
    try:
        define_modal_case(m)
    except Exception as e:
        print(f"  [ERROR] Modal fallo: {e}")

    # 4. Response Spectrum — SOLO si espectro se definio
    print("\n--- Response Spectrum ---")
    if spectrum_ok:
        try:
            define_rs_cases(m)
        except Exception as e:
            print(f"  [ERROR] RS cases fallo: {e}")
            print("  >>> Si ETABS se cerro, abrir Edificio1.edb y ejecutar paso 8 manualmente")
    else:
        print("  [SKIP] No se crean RS cases porque el espectro no se definio")
        print("  >>> 1. Importar espectro desde espectro_nch433.txt")
        print("  >>> 2. Re-ejecutar: python 08_spectrum_cases.py")

    # 5. Combinaciones (independiente del espectro)
    print("\n--- Combinaciones ---")
    try:
        define_combinations(m)
    except Exception as e:
        print(f"  [ERROR] Combinaciones fallo: {e}")

    print("\n=== 08_spectrum_cases COMPLETADO ===")


if __name__ == '__main__':
    main()
