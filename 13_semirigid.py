"""
13_semirigid.py — Generar variante semi-rigida del modelo.

SaveAs → quitar diafragma rigido → re-analizar → mostrar resultados.
Produce: Edificio1_SemiRigido.edb

FIX v3: Import correcto de 12_results (no 'import_helper').
"""
import os
import importlib
import time
from config_helper import get_model, set_units_tonf_m
from config import LOSA_NAME


def remove_diaphragm(m):
    """Quitar diafragma rigido de todas las losas."""
    set_units_tonf_m(m)

    result = m.AreaObj.GetNameList()
    if isinstance(result, (list, tuple)) and len(result) > 1:
        area_names = result[1] if result[1] is not None else []
    else:
        print("  [ERROR] No se pudo obtener lista de areas")
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

        # Intentar remover diafragma
        for dname in ['None', '']:
            try:
                ret = m.AreaObj.SetDiaphragm(area_name, dname)
                if ret == 0:
                    count += 1
                    break
            except Exception:
                continue

    return count


def main():
    m = get_model()
    set_units_tonf_m(m)

    print("\n--- Generar variante semi-rigida ---")

    # 1. SaveAs
    script_dir = os.path.dirname(os.path.abspath(__file__))
    edb_semi = os.path.join(script_dir, 'Edificio1_SemiRigido.edb')

    print(f"  Guardando como: {edb_semi}")
    try:
        ret = m.File.Save(edb_semi)
        print(f"  File.Save: ret={ret}")
    except Exception as e:
        print(f"  [ERROR] Save: {e}")
        return

    # 2. Remover diafragma
    print("\n  Removiendo diafragma rigido...")
    count = remove_diaphragm(m)
    print(f"  Diafragma removido de {count} losas")

    if count == 0:
        print("  [WARN] No se pudo remover diafragma")
        print("  >>> MANUAL: Assign > Shell > Diaphragm > None")
        return

    # 3. Re-guardar
    try:
        m.File.Save(edb_semi)
    except Exception:
        pass

    # 4. Re-analizar
    print("\n  Re-analizando modelo semi-rigido...")
    try:
        t0 = time.time()
        ret = m.Analyze.RunAnalysis()
        dt = time.time() - t0
        print(f"  RunAnalysis: ret={ret} ({dt:.0f}s)")
    except Exception as e:
        print(f"  [WARN] RunAnalysis: {e}")
        print("  >>> Ejecutar manualmente: Analyze > Run Analysis")

    # 5. Resultados basicos
    print("\n  Resultados modelo semi-rigido:")
    try:
        mod_results = importlib.import_module('12_results')
        mod_results.show_modal_results(m)
        mod_results.show_base_shear(m)
    except Exception:
        print("  >>> Ver resultados en ETABS: Display > Show Tables")

    print("\n=== 13_semirigid COMPLETADO ===")
    print(f"  Archivo: {edb_semi}")


if __name__ == '__main__':
    main()
