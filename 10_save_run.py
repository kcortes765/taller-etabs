"""
10_save_run.py — Guardar modelo .EDB y ejecutar analisis.

Idempotente: se puede correr multiples veces. Cada vez sobreescribe el .EDB.
"""
import os
import time
from config_helper import get_model, set_units_tonf_m


def save_model(m, filename='Edificio1.edb'):
    """Guardar modelo como .EDB."""
    set_units_tonf_m(m)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    edb_path = os.path.join(script_dir, filename)

    print(f"  Guardando en: {edb_path}")
    try:
        ret = m.File.Save(edb_path)
        print(f"  File.Save: ret={ret}")
        if ret == 0:
            print(f"[OK] Modelo guardado: {filename}")
            return True
    except Exception as e:
        print(f"  [ERROR] File.Save: {e}")

    # Fallback: intentar sin ruta absoluta
    try:
        ret = m.File.Save(filename)
        print(f"  File.Save (relativo): ret={ret}")
        return ret == 0
    except Exception as e:
        print(f"  [ERROR] File.Save relativo: {e}")

    return False


def run_analysis(m):
    """Ejecutar analisis. Bloquea hasta completar."""
    set_units_tonf_m(m)

    print("  Ejecutando analisis (puede tardar 2-10 min para 20 pisos)...")
    t0 = time.time()

    try:
        ret = m.Analyze.RunAnalysis()
        dt = time.time() - t0
        print(f"  Analyze.RunAnalysis: ret={ret} ({dt:.0f}s)")
        if ret == 0:
            print(f"[OK] Analisis completado en {dt:.0f}s")
            return True
        else:
            print(f"  [WARN] Analisis retorno {ret}, verificar en ETABS")
            return False
    except Exception as e:
        dt = time.time() - t0
        print(f"  [ERROR] RunAnalysis fallo tras {dt:.0f}s: {e}")
        print("  >>> Ejecutar manualmente: Analyze > Run Analysis")
        return False


def main():
    m = get_model()
    print("\n--- Guardar modelo ---")
    save_model(m)
    print("\n--- Ejecutar analisis ---")
    run_analysis(m)
    print("\n=== 10_save_run COMPLETADO ===")


if __name__ == '__main__':
    main()
