"""
02_materials_sections.py — Definir materiales (G30, A630-420H) y secciones.
"""
from config_helper import get_model, set_units_kgf_cm, set_units_tonf_m
from config import (
    FC_KGF_CM2, EC_KGF_CM2, GAMMA_HA, POISSON_CONC,
    FY_KGF_CM2, ES_KGF_CM2, GAMMA_ACERO, POISSON_STEEL,
    VIGA_B, VIGA_H, VIGA_NAME,
    MURO_30_NAME, MURO_30_ESP, MURO_20_NAME, MURO_20_ESP,
    LOSA_NAME, LOSA_ESP,
)


def define_materials(m):
    """Definir hormigon G30 y acero A630-420H."""
    set_units_kgf_cm(m)

    # --- Hormigon G30 (eMatType: 2=Concrete) ---
    ret = m.PropMaterial.SetMaterial('G30', 2)
    print(f"  SetMaterial G30: ret={ret}")

    ret = m.PropMaterial.SetMPIsotropic('G30', EC_KGF_CM2, POISSON_CONC, 9.9e-6)
    print(f"  SetMPIsotropic G30: ret={ret}")

    # Peso especifico: 2.5 tonf/m3 = 0.0025 kgf/cm3
    ret = m.PropMaterial.SetWeightAndMass('G30', 1, GAMMA_HA / 1000.0)
    print(f"  SetWeightAndMass G30: ret={ret}")

    # f'c y modelo constitutivo
    try:
        ret = m.PropMaterial.SetOConcrete_1(
            'G30', FC_KGF_CM2, False, 1.0, 2, 4, 0.002, 0.005, -0.1
        )
        print(f"  SetOConcrete_1 G30: ret={ret}")
    except Exception as e:
        print(f"  [WARN] SetOConcrete_1: {e}")

    # --- Acero A630-420H (eMatType: 6=Rebar) ---
    ret = m.PropMaterial.SetMaterial('A630-420H', 6)
    print(f"  SetMaterial A630-420H: ret={ret}")

    ret = m.PropMaterial.SetMPIsotropic('A630-420H', ES_KGF_CM2, POISSON_STEEL, 1.17e-5)
    print(f"  SetMPIsotropic A630-420H: ret={ret}")

    ret = m.PropMaterial.SetWeightAndMass('A630-420H', 1, GAMMA_ACERO / 1000.0)
    print(f"  SetWeightAndMass A630-420H: ret={ret}")

    try:
        ret = m.PropMaterial.SetORebar_1(
            'A630-420H', FY_KGF_CM2, 6300.0,
            FY_KGF_CM2 / ES_KGF_CM2, 0.09,
            1, 2, 0.01, 0.09, -0.1
        )
        print(f"  SetORebar_1 A630-420H: ret={ret}")
    except Exception as e:
        print(f"  [WARN] SetORebar_1: {e}")

    set_units_tonf_m(m)
    print("[OK] Materiales definidos")


def define_sections(m):
    """Definir secciones de vigas, muros y losas."""
    set_units_tonf_m(m)

    # --- Viga VI20/60G30 ---
    ret = m.PropFrame.SetRectangle(VIGA_NAME, 'G30', VIGA_H, VIGA_B)
    print(f"  SetRectangle {VIGA_NAME}: ret={ret}")

    # J=0 para vigas (practica chilena)
    try:
        ret = m.PropFrame.SetModifiers(VIGA_NAME, [1,1,1,0,1,1,1,1])
        print(f"  Frame modifiers J=0: ret={ret}")
    except Exception as e:
        print(f"  [WARN] Frame modifiers: {e}")

    # --- Muros (eWallPropType=1=Specified, eShellType=1=ShellThin) ---
    ret = m.PropArea.SetWall(MURO_30_NAME, 1, 1, 'G30', MURO_30_ESP)
    print(f"  SetWall {MURO_30_NAME}: ret={ret}")

    ret = m.PropArea.SetWall(MURO_20_NAME, 1, 1, 'G30', MURO_20_ESP)
    print(f"  SetWall {MURO_20_NAME}: ret={ret}")

    # --- Losa (eSlabType=0=Slab, eShellType=1=ShellThin) ---
    ret = m.PropArea.SetSlab(LOSA_NAME, 0, 1, 'G30', LOSA_ESP)
    print(f"  SetSlab {LOSA_NAME}: ret={ret}")

    # Reducir inercia losa al 25% (practica chilena — Lafontaine)
    try:
        ret = m.PropArea.SetModifiers(LOSA_NAME,
            [1.0, 1.0, 1.0, 0.25, 0.25, 0.25, 1.0, 1.0, 1.0, 1.0])
        print(f"  Slab modifiers 25% inercia: ret={ret}")
    except Exception as e:
        print(f"  [WARN] Slab modifiers: {e}")

    print("[OK] Secciones definidas")


def main():
    m = get_model()
    print("\n--- Materiales ---")
    define_materials(m)
    print("\n--- Secciones ---")
    define_sections(m)
    print("\n=== 02_materials_sections COMPLETADO ===")


if __name__ == '__main__':
    main()
