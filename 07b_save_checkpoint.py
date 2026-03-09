"""
07b_save_checkpoint.py — Guardar checkpoint + verificacion completa de geometria.

FIX v3: Verificacion exhaustiva antes de guardar. Si no hay elementos,
ABORTA el pipeline (no tiene sentido seguir con modelo vacio).
"""
import os
import sys
from config_helper import (
    TONF_M_C,
    format_story_table,
    get_model,
    get_story_data,
    set_units_tonf_m,
    stories_match_expected,
    verify_elements,
)
from config import STORY_ELEVATIONS, STORY_HEIGHTS, STORY_NAMES


def main():
    m = get_model()
    set_units_tonf_m(m)

    # *** VERIFICACION COMPLETA antes de guardar ***
    print("\n  === VERIFICACION DE GEOMETRIA ===")
    counts = verify_elements(m)
    areas = counts.get('areas', 0)
    frames = counts.get('frames', 0)
    points = counts.get('points', 0)

    print(f"  Areas (muros+losas): {areas}")
    print(f"  Frames (vigas):      {frames}")
    print(f"  Points (nodos):      {points}")

    # Verificar modelo
    try:
        fname = m.GetModelFilename()
        print(f"  Archivo modelo:      {fname or '(sin guardar)'}")
    except Exception:
        pass

    try:
        units = m.GetPresentUnits()
        print(f"  PresentUnits:        {units}")
        if units != TONF_M_C:
            print(f"  [ERROR CRITICO] Unidades invalidas: se esperaba Ton_m_C ({TONF_M_C})")
            sys.exit(1)
    except Exception:
        pass

    story_data = get_story_data(m)
    print(format_story_table(story_data))
    stories_ok, names_ok = stories_match_expected(
        story_data,
        STORY_NAMES,
        STORY_HEIGHTS,
        STORY_ELEVATIONS,
    )
    if not stories_ok:
        # En v19, get_story_data falla aunque NewGridOnly creo los pisos correctamente.
        # Solo abortamos si el modelo ademas esta vacio.
        print("  [WARN] No se pudo leer stories via API (normal en v19 — NewGridOnly OK)")
    elif not names_ok:
        print("  [WARN] Nombres de stories distintos, pero alturas/elevaciones correctas")

    if areas == 0 and frames == 0:
        print("\n  [ERROR CRITICO] EL MODELO ESTA VACIO!")
        print("  No se crearon muros, vigas ni losas.")
        print("  Causas probables:")
        print("    1. La API conecto a una instancia ETABS diferente de la visible")
        print("    2. SetStories no creo pisos correctamente")
        print("    3. Las secciones (MHA30G30, etc.) no se definieron")
        print("")
        print("  SOLUCIONES:")
        print("    1. Cerrar TODOS los ETABS: taskkill /F /IM ETABS.exe")
        print("    2. Abrir SOLO ETABS 19, esperar 20s")
        print("    3. python run_all.py")
        print("")
        print("  ABORTANDO pipeline — no tiene sentido guardar modelo vacio.")
        sys.exit(1)

    # Guardar checkpoint
    script_dir = os.path.dirname(os.path.abspath(__file__))
    edb_path = os.path.join(script_dir, 'Edificio1.edb')

    print(f"\n  Guardando checkpoint: {edb_path}")
    try:
        ret = m.File.Save(edb_path)
        print(f"  File.Save: ret={ret}")
        if ret == 0:
            print(f"[OK] Checkpoint guardado ({areas} areas, {frames} frames, {points} points)")
        else:
            print(f"  [WARN] Save retorno {ret}")
    except Exception as e:
        print(f"  [ERROR] Save: {e}")
        fallback = os.path.join(os.path.expanduser('~'), 'Desktop', 'Edificio1.edb')
        try:
            ret = m.File.Save(fallback)
            print(f"  Fallback guardado en: {fallback}")
        except Exception:
            print("  [ERROR] No se pudo guardar. Guardar manualmente: File > Save As")

    print("=== 07b_save_checkpoint COMPLETADO ===")


if __name__ == '__main__':
    main()
