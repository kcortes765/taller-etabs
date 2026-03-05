"""
12_results.py — Extraer y mostrar resumen de resultados post-analisis.

Muestra: periodos, masa participativa, peso sismico, corte basal, drift.
"""
from config_helper import get_model, set_units_tonf_m
from config import (
    N_STORIES, STORY_NAMES, STORY_HEIGHTS, STORY_ELEVATIONS,
    AREA_PLANTA, G_ACCEL, RO_MUROS,
)


def show_modal_results(m):
    """Mostrar periodos y masa participativa."""
    print("\n" + "=" * 60)
    print("  PERIODOS FUNDAMENTALES Y MASA PARTICIPATIVA")
    print("=" * 60)

    try:
        m.Results.Setup.DeselectAllCasesAndCombosForOutput()
    except Exception:
        pass
    try:
        m.Results.Setup.SetCaseSelectedForOutput('Modal')
    except Exception:
        try:
            m.Results.Setup.SetCaseSelectedForOutput('MODAL')
        except Exception:
            pass

    # Intentar leer masas participativas
    result = None
    for func in [
        lambda: m.Results.ModalParticipatingMassRatios(
            0, [], [], [], [], [], [], [], [], [], [], [], [], [], 0),
        lambda: m.Results.ModalParticipatingMassRatios(),
    ]:
        try:
            result = func()
            break
        except Exception:
            pass

    if result and len(result) > 10:
        _print_modal_table(result)
    else:
        # Fallback: solo periodos
        for func in [
            lambda: m.Results.ModalPeriod(0, [], [], [], [], [], 0),
            lambda: m.Results.ModalPeriod(),
        ]:
            try:
                result = func()
                _print_periods_only(result)
                return
            except Exception:
                pass
        print("  [ERROR] No se pudieron leer resultados modales")


def _print_modal_table(result):
    """Imprimir tabla de modos con masas participativas."""
    vals = list(result)

    # Encontrar listas de datos
    lists = [(i, v) for i, v in enumerate(vals)
             if isinstance(v, (list, tuple)) and len(v) > 0]

    if len(lists) < 3:
        print(f"  Resultado raw: {result}")
        return

    # Heuristica: buscar periodos, luego Ux, Uy, SumUx, SumUy
    periods = None
    data_start = None
    for idx, (i, v) in enumerate(lists):
        try:
            floats = [float(x) for x in v]
            if all(x > 0 for x in floats) and max(floats) < 100 and periods is None:
                periods = floats
                data_start = idx
                break
        except (ValueError, TypeError):
            pass

    if periods is None:
        print(f"  No se encontraron periodos en resultado")
        return

    n = len(periods)
    # Extraer listas siguientes como Ux, Uy, Uz, SumUx, SumUy, SumUz
    data_lists = []
    for j in range(data_start + 1, len(lists)):
        _, v = lists[j]
        if len(v) == n:
            try:
                data_lists.append([float(x) for x in v])
            except (ValueError, TypeError):
                pass

    ux = data_lists[0] if len(data_lists) > 0 else [0] * n
    uy = data_lists[1] if len(data_lists) > 1 else [0] * n

    # Buscar SumUx, SumUy (listas crecientes)
    sum_ux = None
    sum_uy = None
    for dl in data_lists:
        if all(dl[i] <= dl[i+1] + 0.001 for i in range(len(dl)-1)) and dl[-1] > 0.5:
            if sum_ux is None:
                sum_ux = dl
            elif sum_uy is None:
                sum_uy = dl
                break

    print(f"\n  {'Modo':>4} {'T (s)':>8} {'Ux':>8} {'Uy':>8} {'SumUx':>8} {'SumUy':>8}")
    print(f"  {'-'*4} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    show_n = min(15, n)
    for i in range(show_n):
        sux = f"{sum_ux[i]:.2%}" if sum_ux else "---"
        suy = f"{sum_uy[i]:.2%}" if sum_uy else "---"
        print(f"  {i+1:4d} {periods[i]:8.4f} {ux[i]:8.4f} {uy[i]:8.4f} {sux:>8} {suy:>8}")

    # Verificar 90% acumulado
    if sum_ux and sum_uy:
        for i in range(n):
            if sum_ux[i] >= 0.90 and sum_uy[i] >= 0.90:
                print(f"\n  90% masa alcanzada en modo {i+1}")
                break


def _print_periods_only(result):
    """Imprimir solo periodos."""
    vals = list(result)
    for v in vals:
        if isinstance(v, (list, tuple)) and len(v) > 0:
            try:
                periods = [float(x) for x in v]
                if all(x > 0 for x in periods) and max(periods) < 100:
                    print(f"\n  {'Modo':>4} {'T (s)':>8}")
                    print(f"  {'-'*4} {'-'*8}")
                    for i, p in enumerate(periods[:15]):
                        print(f"  {i+1:4d} {p:8.4f}")
                    return
            except (ValueError, TypeError):
                pass


def show_base_shear(m):
    """Mostrar corte basal para SEx y SEy."""
    print("\n" + "=" * 60)
    print("  CORTE BASAL")
    print("=" * 60)

    for case_name in ['SEx', 'SEy']:
        try:
            m.Results.Setup.DeselectAllCasesAndCombosForOutput()
            m.Results.Setup.SetCaseSelectedForOutput(case_name)
        except Exception:
            continue

        for func in [
            lambda: m.Results.BaseReact(0, [], [], [], [], [], [], [], [], 0),
            lambda: m.Results.BaseReact(),
        ]:
            try:
                result = func()
                _print_base_react(case_name, result)
                break
            except Exception:
                pass
        else:
            print(f"  {case_name}: No se pudo leer corte basal")


def _print_base_react(case_name, result):
    """Parsear e imprimir reacciones basales."""
    vals = list(result)
    # Buscar valores de fuerza (floats grandes)
    forces = []
    for v in vals:
        if isinstance(v, (list, tuple)):
            try:
                forces.append([float(x) for x in v])
            except (ValueError, TypeError):
                pass
        elif isinstance(v, (int, float)):
            forces.append(v)

    # El formato tipico es: (NumberResults, [Fx], [Fy], [Fz], [Mx], [My], [Mz], ...)
    if len(forces) >= 3 and all(isinstance(f, list) for f in forces[:3]):
        fx = forces[0][0] if forces[0] else 0
        fy = forces[1][0] if forces[1] else 0
        fz = forces[2][0] if forces[2] else 0
        print(f"  {case_name}: Fx={fx:.1f} tonf, Fy={fy:.1f} tonf, Fz={fz:.1f} tonf")
    else:
        print(f"  {case_name}: resultado raw = {result}")


def show_story_drifts(m):
    """Mostrar drift por piso."""
    print("\n" + "=" * 60)
    print("  DRIFT POR PISO")
    print("=" * 60)

    for case_name in ['SEx', 'SEy']:
        try:
            m.Results.Setup.DeselectAllCasesAndCombosForOutput()
            m.Results.Setup.SetCaseSelectedForOutput(case_name)
        except Exception:
            continue

        result = None
        for func in [
            lambda: m.Results.StoryDrifts(
                0, [], [], [], [], [], [], [], [], [], 0),
            lambda: m.Results.StoryDrifts(),
        ]:
            try:
                result = func()
                break
            except Exception:
                pass

        if result:
            print(f"\n  --- {case_name} ---")
            _print_drifts(result, case_name)
        else:
            print(f"  {case_name}: No se pudo leer drift")
            print(f"  >>> MANUAL: Display > Show Tables > Story Drifts")


def _print_drifts(result, case_name):
    """Parsear e imprimir drifts."""
    vals = list(result)

    # Buscar listas de strings (story names) y floats (drifts)
    stories = None
    drifts = []
    for v in vals:
        if isinstance(v, (list, tuple)) and len(v) > 0:
            if isinstance(v[0], str) and stories is None:
                stories = list(v)
            else:
                try:
                    drifts.append([float(x) for x in v])
                except (ValueError, TypeError):
                    pass

    if stories and drifts:
        # Drift X o Y segun el caso
        drift_vals = drifts[0] if drifts else [0] * len(stories)

        print(f"  {'Piso':<10} {'Drift':>10} {'h(m)':>6} {'Ratio':>10} {'<0.002':>8}")
        print(f"  {'-'*10} {'-'*10} {'-'*6} {'-'*10} {'-'*8}")

        for i, s in enumerate(stories):
            d = drift_vals[i] if i < len(drift_vals) else 0
            # Buscar altura del piso
            h = 2.6  # default
            for j, sn in enumerate(STORY_NAMES):
                if sn in s or s in sn:
                    h = STORY_HEIGHTS[j]
                    break

            ratio = f"1/{1/d:.0f}" if d > 0 else "---"
            ok = "OK" if d < 0.002 else "EXCEDE"
            print(f"  {s:<10} {d:10.6f} {h:6.1f} {ratio:>10} {ok:>8}")
    else:
        print(f"  Resultado raw (primeros 5): {vals[:5]}")


def show_seismic_weight(m):
    """Estimar peso sismico del edificio."""
    print("\n" + "=" * 60)
    print("  PESO SISMICO")
    print("=" * 60)

    # Intentar leer reaccion base para carga muerta
    try:
        m.Results.Setup.DeselectAllCasesAndCombosForOutput()
        m.Results.Setup.SetCaseSelectedForOutput('PP')
    except Exception:
        pass

    for func in [
        lambda: m.Results.BaseReact(0, [], [], [], [], [], [], [], [], 0),
        lambda: m.Results.BaseReact(),
    ]:
        try:
            result = func()
            vals = list(result)
            # Buscar Fz (fuerza vertical)
            for v in vals:
                if isinstance(v, (list, tuple)):
                    try:
                        fz_list = [float(x) for x in v]
                        fz = max(abs(x) for x in fz_list)
                        if fz > 100:  # probablemente peso total en tonf
                            print(f"  Reaccion vertical PP: {fz:.0f} tonf")
                            print(f"  Peso/area: {fz / AREA_PLANTA:.2f} tonf/m2")
                            if 0.8 <= fz / AREA_PLANTA / N_STORIES <= 1.2:
                                print(f"  [OK] Peso razonable (~1 tonf/m2/piso)")
                            return
                    except (ValueError, TypeError):
                        pass
            print(f"  Resultado raw: {result}")
            return
        except Exception:
            pass

    print("  [WARN] No se pudo leer peso sismico")
    print("  >>> MANUAL: Display > Show Tables > Base Reactions (caso PP)")


def main():
    m = get_model()
    show_modal_results(m)
    show_base_shear(m)
    show_story_drifts(m)
    show_seismic_weight(m)
    print("\n=== 12_results COMPLETADO ===")


if __name__ == '__main__':
    main()
