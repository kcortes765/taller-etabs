"""
03_walls.py — Dibujar todos los muros del Edificio 1 en todos los pisos.

FIX v3: Verificacion post-creacion con GetNameList + RefreshView.
"""
from config_helper import get_model, set_units_tonf_m, verify_elements, refresh_view
from config import (
    MUROS_DIR_Y, MUROS_DIR_X,
    MURO_30_NAME, MURO_30_ESP, MURO_20_NAME,
    STORY_NAMES, STORY_ELEVATIONS,
)


def get_section(esp):
    if abs(esp - 0.30) < 0.01:
        return MURO_30_NAME
    return MURO_20_NAME


def draw_walls(m):
    set_units_tonf_m(m)

    # Conteo ANTES de crear
    pre = verify_elements(m)
    pre_areas = pre.get('areas', 0)

    count = 0
    errors = 0

    for i, story in enumerate(STORY_NAMES):
        z_bot = 0.0 if i == 0 else STORY_ELEVATIONS[i - 1]
        z_top = STORY_ELEVATIONS[i]

        # Muros dir Y (x fijo, y varia)
        for eje, x, y0, y1, esp in MUROS_DIR_Y:
            sec = get_section(esp)
            try:
                result = m.AreaObj.AddByCoord(
                    4,
                    [x, x, x, x],
                    [y0, y1, y1, y0],
                    [z_bot, z_bot, z_top, z_top],
                    '', sec, '', 'Global'
                )
                ret = result[-1] if isinstance(result, (list, tuple)) else result
                if ret == 0:
                    count += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  [ERR] Muro Y eje {eje} {story}: {e}")

        # Muros dir X (y fijo, x varia)
        for eje, y, x0, x1, esp in MUROS_DIR_X:
            sec = get_section(esp)
            try:
                result = m.AreaObj.AddByCoord(
                    4,
                    [x0, x1, x1, x0],
                    [y, y, y, y],
                    [z_bot, z_bot, z_top, z_top],
                    '', sec, '', 'Global'
                )
                ret = result[-1] if isinstance(result, (list, tuple)) else result
                if ret == 0:
                    count += 1
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  [ERR] Muro X eje {eje} {story}: {e}")

    n_por_piso = len(MUROS_DIR_Y) + len(MUROS_DIR_X)
    print(f"  API reporta: {count} muros creados ({n_por_piso}/piso x {len(STORY_NAMES)} pisos)")
    if errors:
        print(f"  [WARN] {errors} errores")

    # *** VERIFICACION: confirmar que los elementos existen realmente ***
    post = verify_elements(m)
    post_areas = post.get('areas', 0)
    muros_reales = post_areas - pre_areas
    print(f"  Verificacion: {muros_reales} areas nuevas en modelo (antes={pre_areas}, ahora={post_areas})")

    if muros_reales == 0 and count > 0:
        print("  [ERROR CRITICO] La API reporto exito pero NO se crearon muros!")
        print("  >>> Probable: conectado a instancia ETABS incorrecta")
        print("  >>> Solucion: cerrar TODO ETABS, abrir solo v19, reintentar")

    refresh_view(m)
    print(f"[OK] {muros_reales} muros verificados en modelo")


def main():
    m = get_model()
    print("\n--- Dibujando muros ---")
    draw_walls(m)
    print("\n=== 03_walls COMPLETADO ===")


if __name__ == '__main__':
    main()
