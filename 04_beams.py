"""
04_beams.py — Dibujar vigas VI20/60G30 en todos los pisos.

FIX v3: Verificacion post-creacion + RefreshView.
"""
from config_helper import get_model, set_units_tonf_m, verify_elements, refresh_view
from config import VIGAS, VIGA_NAME, STORY_NAMES, STORY_ELEVATIONS


def draw_beams(m):
    set_units_tonf_m(m)

    # Conteo ANTES
    pre = verify_elements(m)
    pre_frames = pre.get('frames', 0)

    count = 0
    errors = 0

    for i, story in enumerate(STORY_NAMES):
        z = STORY_ELEVATIONS[i]

        for y_coord, x_start, x_end in VIGAS:
            try:
                result = m.FrameObj.AddByCoord(
                    x_start, y_coord, z,
                    x_end, y_coord, z,
                    '', VIGA_NAME, '', 'Global'
                )
                ret = result[-1] if isinstance(result, (list, tuple)) else result
                if ret == 0:
                    count += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  [ERR] Viga {story}: {e}")

    print(f"  API reporta: {count} vigas creadas ({len(VIGAS)}/piso x {len(STORY_NAMES)} pisos)")
    if errors:
        print(f"  [WARN] {errors} errores")

    # *** VERIFICACION ***
    post = verify_elements(m)
    post_frames = post.get('frames', 0)
    vigas_reales = post_frames - pre_frames
    print(f"  Verificacion: {vigas_reales} frames nuevos (antes={pre_frames}, ahora={post_frames})")

    if vigas_reales == 0 and count > 0:
        print("  [ERROR CRITICO] API reporto exito pero NO se crearon vigas!")
        print("  >>> Probable: instancia ETABS incorrecta")

    refresh_view(m)
    print(f"[OK] {vigas_reales} vigas verificadas en modelo")


def main():
    m = get_model()
    print("\n--- Dibujando vigas ---")
    draw_beams(m)
    print("\n=== 04_beams COMPLETADO ===")


if __name__ == '__main__':
    main()
