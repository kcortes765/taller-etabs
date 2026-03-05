"""
11_adjust_Rstar.py — Leer T* del analisis modal, calcular R*, actualizar
escala de todos los RS cases, re-guardar y re-analizar.

Requiere que el analisis haya corrido al menos una vez (paso 10).
"""
import os
import time
from config_helper import get_model, set_units_tonf_m
from config import RO_MUROS, G_ACCEL, calc_R_star


def get_modal_results(m):
    """Leer periodos y masas participativas del analisis modal.

    Retorna dict con:
      periods: lista de periodos
      ux: lista de masa participativa en X
      uy: lista de masa participativa en Y
      rz: lista de masa participativa rotacional Z
    """
    set_units_tonf_m(m)

    # Seleccionar caso Modal para output
    try:
        m.Results.Setup.DeselectAllCasesAndCombosForOutput()
        m.Results.Setup.SetCaseSelectedForOutput('Modal')
    except Exception:
        try:
            m.Results.Setup.DeselectAllCasesAndCombosForOutput()
            m.Results.Setup.SetCaseSelectedForOutput('MODAL')
        except Exception as e:
            print(f"  [WARN] No se pudo seleccionar caso Modal: {e}")

    # Intentar leer masas participativas
    methods = [
        ('ModalParticipatingMassRatios',
         lambda: m.Results.ModalParticipatingMassRatios(
             0, [], [], [], [], [], [], [], [], [], [], [], [], [], 0)),
        ('ModalParticipatingMassRatios (sin args)',
         lambda: m.Results.ModalParticipatingMassRatios()),
        ('ModalParticipatingMassRatios (1 arg)',
         lambda: m.Results.ModalParticipatingMassRatios(0)),
    ]

    for desc, func in methods:
        try:
            result = func()
            print(f"  {desc}: len={len(result) if result else 0}")
            if result and len(result) > 5:
                return _parse_modal_mass_ratios(result)
        except AttributeError:
            print(f"  {desc}: metodo no existe")
        except Exception as e:
            print(f"  {desc}: {e}")

    # Fallback: leer solo periodos (sin masas participativas)
    print("  Fallback: leyendo solo periodos modales...")
    period_methods = [
        ('ModalPeriod', lambda: m.Results.ModalPeriod(0, [], [], [], [], [], 0)),
        ('ModalPeriod (sin args)', lambda: m.Results.ModalPeriod()),
    ]

    for desc, func in period_methods:
        try:
            result = func()
            print(f"  {desc}: len={len(result) if result else 0}")
            if result:
                return _parse_modal_periods(result)
        except AttributeError:
            pass
        except Exception as e:
            print(f"  {desc}: {e}")

    print("  [ERROR] No se pudieron leer resultados modales")
    return None


def _parse_modal_mass_ratios(result):
    """Parsear resultado de ModalParticipatingMassRatios.

    Formato ETABS API (tipico):
    result = (NumberResults, LoadCase[], StepType[], StepNum[],
              Period[], Ux[], Uy[], Uz[],
              SumUx[], SumUy[], SumUz[],
              Rx[], Ry[], Rz[],
              SumRx[], SumRy[], SumRz[], ret)

    Pero el formato exacto varia entre versiones.
    """
    vals = list(result)

    # Buscar la lista de periodos (deberia ser una lista de floats > 0)
    periods = None
    ux = None
    uy = None

    for i, v in enumerate(vals):
        if isinstance(v, (list, tuple)) and len(v) > 0:
            # Verificar si son periodos (floats positivos)
            try:
                floats = [float(x) for x in v]
                if all(x > 0 for x in floats) and periods is None:
                    if max(floats) > 0.01 and max(floats) < 100:  # periodos razonables
                        periods = floats
                        # Los siguientes deberian ser Ux, Uy
                        for j in range(i+1, min(i+4, len(vals))):
                            if isinstance(vals[j], (list, tuple)):
                                try:
                                    f = [float(x) for x in vals[j]]
                                    if all(0 <= x <= 1 for x in f):
                                        if ux is None:
                                            ux = f
                                        elif uy is None:
                                            uy = f
                                            break
                                except (ValueError, TypeError):
                                    pass
            except (ValueError, TypeError):
                pass

    if periods:
        return {
            'periods': periods,
            'ux': ux or [0] * len(periods),
            'uy': uy or [0] * len(periods),
        }

    return None


def _parse_modal_periods(result):
    """Parsear resultado de ModalPeriod (solo periodos, sin masas)."""
    vals = list(result)

    for v in vals:
        if isinstance(v, (list, tuple)) and len(v) > 0:
            try:
                floats = [float(x) for x in v]
                if all(x > 0 for x in floats) and max(floats) < 100:
                    return {
                        'periods': floats,
                        'ux': None,
                        'uy': None,
                    }
            except (ValueError, TypeError):
                pass

    return None


def find_T_star(modal_data):
    """Encontrar T*x y T*y (periodos fundamentales en cada direccion).

    Si hay masas participativas: T* = periodo del modo con mayor masa.
    Si no hay masas: T*x = T1, T*y = T2 (estimacion).
    """
    periods = modal_data['periods']
    ux = modal_data.get('ux')
    uy = modal_data.get('uy')

    if ux and uy and len(ux) == len(periods):
        # Modo con maxima masa en X
        idx_x = ux.index(max(ux))
        Tx_star = periods[idx_x]

        # Modo con maxima masa en Y
        idx_y = uy.index(max(uy))
        Ty_star = periods[idx_y]

        print(f"  T*x = {Tx_star:.4f}s (modo {idx_x+1}, Ux={ux[idx_x]:.2%})")
        print(f"  T*y = {Ty_star:.4f}s (modo {idx_y+1}, Uy={uy[idx_y]:.2%})")
    else:
        # Sin masas participativas: asumir T1=X, T2=Y (o viceversa)
        Tx_star = periods[0]
        Ty_star = periods[1] if len(periods) > 1 else periods[0]
        print(f"  T*x ≈ {Tx_star:.4f}s (modo 1, sin datos de masa)")
        print(f"  T*y ≈ {Ty_star:.4f}s (modo 2, sin datos de masa)")
        print("  [WARN] Sin masas participativas. Verificar T* manualmente.")

    return Tx_star, Ty_star


def update_rs_scale(m, case_name, direction, R_star):
    """Actualizar escala del RS case: g / R*."""
    new_sf = G_ACCEL / R_star

    # Intentar multiples firmas
    attempts = [
        lambda: m.LoadCases.ResponseSpectrum.SetLoads(
            case_name, 1, [direction], ['Espectro_NCh433'],
            [new_sf], [''], [0.0]),
        lambda: m.LoadCases.ResponseSpectrum.SetLoads(
            case_name, 1, [direction], ['Espectro_NCh433'], [new_sf]),
    ]

    for func in attempts:
        try:
            ret = func()
            print(f"  {case_name}: R*={R_star:.2f}, SF={new_sf:.4f} m/s2, ret={ret}")
            return True
        except Exception:
            continue

    print(f"  [ERROR] No se pudo actualizar escala de {case_name}")
    print(f"  >>> MANUAL: Edit RS case '{case_name}', Scale Factor = {new_sf:.4f}")
    return False


def main():
    m = get_model()

    print("\n--- Leer periodos modales ---")
    modal_data = get_modal_results(m)
    if modal_data is None:
        print("  [ERROR] No hay resultados modales. Ejecutar paso 10 primero.")
        print("  >>> Si el analisis corrio, verificar resultados en ETABS:")
        print("      Display > Show Tables > Modal Participating Mass Ratios")
        return

    # Mostrar primeros modos
    print(f"\n  Primeros periodos: {[f'{p:.3f}' for p in modal_data['periods'][:5]]}")

    print("\n--- Determinar T* ---")
    Tx_star, Ty_star = find_T_star(modal_data)

    print("\n--- Calcular R* ---")
    Rx_star = calc_R_star(RO_MUROS, Tx_star)
    Ry_star = calc_R_star(RO_MUROS, Ty_star)
    print(f"  Ro = {RO_MUROS}")
    print(f"  R*x = {Rx_star:.2f} (T*x={Tx_star:.3f}s)")
    print(f"  R*y = {Ry_star:.2f} (T*y={Ty_star:.3f}s)")

    print("\n--- Actualizar escala RS cases ---")
    update_rs_scale(m, 'SEx', 'U1', Rx_star)
    update_rs_scale(m, 'SEy', 'U2', Ry_star)

    # Re-guardar y re-analizar
    print("\n--- Re-guardar modelo ---")
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        edb_path = os.path.join(script_dir, 'Edificio1.edb')
        ret = m.File.Save(edb_path)
        print(f"  File.Save: ret={ret}")
    except Exception as e:
        print(f"  [WARN] Save: {e}")

    print("\n--- Re-analizar con R* ---")
    try:
        t0 = time.time()
        ret = m.Analyze.RunAnalysis()
        dt = time.time() - t0
        print(f"  RunAnalysis: ret={ret} ({dt:.0f}s)")
    except Exception as e:
        print(f"  [WARN] RunAnalysis: {e}")
        print("  >>> Ejecutar manualmente: Analyze > Run Analysis")

    print("\n=== 11_adjust_Rstar COMPLETADO ===")
    print(f"  T*x={Tx_star:.3f}s → R*x={Rx_star:.2f}")
    print(f"  T*y={Ty_star:.3f}s → R*y={Ry_star:.2f}")


if __name__ == '__main__':
    main()
