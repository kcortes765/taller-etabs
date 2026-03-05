"""
07b_save_checkpoint.py — Guardar checkpoint de geometria antes de fase analisis.
Previene perder trabajo si ETABS crashea en pasos 8-9.
"""
import os
from config_helper import get_model, set_units_tonf_m


def main():
    m = get_model()
    set_units_tonf_m(m)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    edb_path = os.path.join(script_dir, 'Edificio1.edb')

    print(f"  Guardando checkpoint: {edb_path}")
    try:
        ret = m.File.Save(edb_path)
        print(f"  File.Save: ret={ret}")
        if ret == 0:
            print("[OK] Checkpoint guardado")
        else:
            print(f"  [WARN] Save retorno {ret}")
    except Exception as e:
        print(f"  [ERROR] Save: {e}")
        # Intentar guardar en directorio del usuario
        fallback = os.path.join(os.path.expanduser('~'), 'Desktop', 'Edificio1.edb')
        try:
            ret = m.File.Save(fallback)
            print(f"  Fallback guardado en: {fallback}")
        except Exception:
            print("  [ERROR] No se pudo guardar. Guardar manualmente: File > Save As")

    print("=== 07b_save_checkpoint COMPLETADO ===")


if __name__ == '__main__':
    main()
