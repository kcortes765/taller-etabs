"""
08_spectrum_cases.py — Espectro NCh433+DS61, caso modal, response spectrum,
fuente de masa, combinaciones NCh3171.
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
    """Definir funcion de espectro en ETABS."""
    set_units_tonf_m(m)
    T_vals, Sa_vals = build_elastic_spectrum()

    # Intentar Func.ResponseSpectrum.SetUser (ETABS v19)
    try:
        ret = m.Func.ResponseSpectrum.SetUser(
            'Espectro_NCh433', len(T_vals), T_vals, Sa_vals, 0.05
        )
        print(f"  Func.ResponseSpectrum.SetUser: ret={ret}")
    except Exception:
        # Fallback: Func.FuncRS.SetUser
        try:
            ret = m.Func.FuncRS.SetUser(
                'Espectro_NCh433', len(T_vals), T_vals, Sa_vals, 0.05
            )
            print(f"  Func.FuncRS.SetUser (fallback): ret={ret}")
        except Exception as e:
            print(f"  [ERROR] No se pudo definir espectro: {e}")
            return

    print(f"[OK] Espectro: {len(T_vals)} puntos (T=0 a 5s)")
    print(f"     Sa(T=0)={Sa_vals[0]:.3f}g, Sa(T=1s)={Sa_vals[20]:.4f}g")


def define_mass_source(m):
    """Fuente de masa: selfweight + 100%TERP + 25%SCP."""
    try:
        ret = m.PropMass.SetMassSource_1(
            True,             # IncludeElements (self weight)
            False,            # IncludeAddedMass
            True,             # IncludeLoads
            2,                # NumLoads
            ['TERP', 'SCP'],  # LoadPatterns
            [1.0, 0.25]       # Scale factors
        )
        print(f"  PropMass.SetMassSource_1: ret={ret}")
        print("[OK] Fuente de masa sismica definida")
    except Exception as e:
        print(f"  [WARN] Mass source: {e}")
        print("  Definir manualmente: Define > Mass Source")


def define_modal_case(m):
    """Caso modal Eigen con suficientes modos."""
    n_modes = 60  # suficiente para edificio 20 pisos

    try:
        ret = m.LoadCases.ModalEigen.SetCase('Modal')
        print(f"  ModalEigen.SetCase: ret={ret}")
    except Exception as e:
        print(f"  [WARN] SetCase Modal: {e}")

    try:
        ret = m.LoadCases.ModalEigen.SetNumberModes('Modal', n_modes, 1)
        print(f"  SetNumberModes({n_modes}): ret={ret}")
    except Exception as e:
        print(f"  [WARN] SetNumberModes: {e}")

    print(f"[OK] Caso modal: {n_modes} modos")


def define_rs_cases(m):
    """Casos Response Spectrum (SEx, SEy)."""
    set_units_tonf_m(m)

    # Factor escala: g = 9.81 (convierte Sa/g a m/s2)
    # Nota: R* se ajusta despues de conocer T* (tras primer analisis)
    sf = G_ACCEL  # 9.81 m/s2

    for case_name, direction in [('SEx', 'U1'), ('SEy', 'U2')]:
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
            print(f"  [WARN] SetModalCase {case_name}: {e}")

        # Asignar espectro y direccion
        try:
            ret = m.LoadCases.ResponseSpectrum.SetLoads(
                case_name,
                1,                       # NumberLoads
                [direction],             # LoadName (U1 o U2)
                ['Espectro_NCh433'],     # Func
                [sf],                    # Scale factor
                [''],                    # CSys (Global)
                [0.0],                   # Ang
            )
            print(f"  SetLoads '{case_name}': ret={ret}")
        except Exception as e:
            print(f"  [ERROR] SetLoads {case_name}: {e}")

        # CQC
        try:
            ret = m.LoadCases.ResponseSpectrum.SetModalComb(case_name, 1, 0.0, 0.0)
            print(f"  SetModalComb CQC: ret={ret}")
        except Exception as e:
            print(f"  [WARN] SetModalComb: {e}")

        # Damping 5%
        try:
            ret = m.LoadCases.ResponseSpectrum.SetDampConstant(case_name, 0.05)
            print(f"  SetDampConstant 5%: ret={ret}")
        except Exception as e:
            print(f"  [WARN] SetDampConstant: {e}")

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
    print("\n--- Espectro NCh433 ---")
    define_spectrum(m)
    print("\n--- Fuente de masa ---")
    define_mass_source(m)
    print("\n--- Caso modal ---")
    define_modal_case(m)
    print("\n--- Response Spectrum ---")
    define_rs_cases(m)
    print("\n--- Combinaciones ---")
    define_combinations(m)
    print("\n=== 08_spectrum_cases COMPLETADO ===")


if __name__ == '__main__':
    main()
