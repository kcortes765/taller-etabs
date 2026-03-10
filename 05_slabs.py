"""
05_slabs.py — Dibujar losas Losa15G30 en todos los panos.

FIX v3: Verificacion post-creacion + RefreshView.
"""
from config_helper import get_model, set_units_tonf_m, unlock_model, verify_elements, refresh_view
from config import (
    LOSA_NAME,
    STORY_NAMES,
    STORY_ELEVATIONS,
    SLAB_PANELS_FLOOR,
    SLAB_PANELS_ROOF,
)


def draw_slabs(m):
    set_units_tonf_m(m)

    # Conteo ANTES
    pre = verify_elements(m)
    pre_areas = pre.get('areas', 0)

    count = 0
    errors = 0

    floor_panel_count = 0
    roof_panel_count = 0

    for i, story in enumerate(STORY_NAMES):
        z = STORY_ELEVATIONS[i]
        panels = SLAB_PANELS_ROOF if i == len(STORY_NAMES) - 1 else SLAB_PANELS_FLOOR
        if i == len(STORY_NAMES) - 1:
            roof_panel_count += len(panels)
        else:
            floor_panel_count += len(panels)

        for x1, y1, x2, y2 in panels:
            try:
                result = m.AreaObj.AddByCoord(
                    4,
                    [x1, x2, x2, x1],
                    [y1, y1, y2, y2],
                    [z, z, z, z],
                    '', LOSA_NAME, '', 'Global'
                )
                ret = result[-1] if isinstance(result, (list, tuple)) else result
                if ret == 0:
                    count += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  [ERR] Losa {story}: {e}")

    expected = floor_panel_count + roof_panel_count
    print(
        f"  API reporta: {count} losas creadas "
        f"({len(SLAB_PANELS_FLOOR)}/piso tipo x {len(STORY_NAMES) - 1} + "
        f"{len(SLAB_PANELS_ROOF)}/techo = {expected})"
    )
    if errors:
        print(f"  [WARN] {errors} errores")

    # *** VERIFICACION ***
    post = verify_elements(m)
    post_areas = post.get('areas', 0)
    losas_reales = post_areas - pre_areas
    print(f"  Verificacion: {losas_reales} areas nuevas (antes={pre_areas}, ahora={post_areas})")

    if losas_reales == 0 and count > 0:
        print("  [ERROR CRITICO] API reporto exito pero NO se crearon losas!")
        print("  >>> Probable: instancia ETABS incorrecta")

    refresh_view(m)
    print(f"[OK] {losas_reales} losas verificadas en modelo")


def main():
    m = get_model()
    unlock_model(m)
    print("\n--- Dibujando losas ---")
    draw_slabs(m)
    print("\n=== 05_slabs COMPLETADO ===")


if __name__ == '__main__':
    main()
