"""
05_slabs.py — Dibujar losas Losa15G30 en todos los panos.

FIX v3: Verificacion post-creacion + RefreshView.
"""
from config_helper import get_model, set_units_tonf_m, verify_elements, refresh_view
from config import GRID_X, GRID_Y, LOSA_NAME, STORY_NAMES, STORY_ELEVATIONS

# Panos de losa: (x1, y1, x2, y2) rectangulos en planta
SLAB_PANELS = [
    # Zona A-B (franja inferior, altura 0.701m)
    (GRID_X['1'],  GRID_Y['A'], GRID_X['3'],  GRID_Y['B']),
    (GRID_X['3'],  GRID_Y['A'], GRID_X['5'],  GRID_Y['B']),
    (GRID_X['5'],  GRID_Y['A'], GRID_X['7'],  GRID_Y['B']),
    (GRID_X['7'],  GRID_Y['A'], GRID_X['10'], GRID_Y['B']),
    (GRID_X['10'], GRID_Y['A'], GRID_X['13'], GRID_Y['B']),
    (GRID_X['13'], GRID_Y['A'], GRID_X['15'], GRID_Y['B']),
    (GRID_X['15'], GRID_Y['A'], GRID_X['17'], GRID_Y['B']),

    # Zona B-C (panos grandes)
    (GRID_X['1'],  GRID_Y['B'], GRID_X['3'],  GRID_Y['C']),
    (GRID_X['3'],  GRID_Y['B'], GRID_X['5'],  GRID_Y['C']),
    (GRID_X['5'],  GRID_Y['B'], GRID_X['7'],  GRID_Y['C']),
    (GRID_X['7'],  GRID_Y['B'], GRID_X['10'], GRID_Y['C']),
    (GRID_X['10'], GRID_Y['B'], GRID_X['13'], GRID_Y['C']),
    (GRID_X['13'], GRID_Y['B'], GRID_X['15'], GRID_Y['C']),
    (GRID_X['15'], GRID_Y['B'], GRID_X['17'], GRID_Y['C']),

    # Zona C-D
    (GRID_X['1'],  GRID_Y['C'], GRID_X['3'],  GRID_Y['D']),
    (GRID_X['3'],  GRID_Y['C'], GRID_X['5'],  GRID_Y['D']),
    (GRID_X['5'],  GRID_Y['C'], GRID_X['7'],  GRID_Y['D']),
    (GRID_X['7'],  GRID_Y['C'], GRID_X['10'], GRID_Y['D']),
    (GRID_X['10'], GRID_Y['C'], GRID_X['13'], GRID_Y['D']),
    (GRID_X['13'], GRID_Y['C'], GRID_X['15'], GRID_Y['D']),
    (GRID_X['15'], GRID_Y['C'], GRID_X['17'], GRID_Y['D']),

    # Zona D-E
    (GRID_X['1'],  GRID_Y['D'], GRID_X['3'],  GRID_Y['E']),
    (GRID_X['3'],  GRID_Y['D'], GRID_X['5'],  GRID_Y['E']),
    (GRID_X['5'],  GRID_Y['D'], GRID_X['7'],  GRID_Y['E']),
    (GRID_X['7'],  GRID_Y['D'], GRID_X['10'], GRID_Y['E']),
    (GRID_X['10'], GRID_Y['D'], GRID_X['13'], GRID_Y['E']),
    (GRID_X['13'], GRID_Y['D'], GRID_X['15'], GRID_Y['E']),
    (GRID_X['15'], GRID_Y['D'], GRID_X['17'], GRID_Y['E']),

    # Zona E-F
    (GRID_X['1'],  GRID_Y['E'], GRID_X['3'],  GRID_Y['F']),
    (GRID_X['3'],  GRID_Y['E'], GRID_X['5'],  GRID_Y['F']),
    (GRID_X['5'],  GRID_Y['E'], GRID_X['7'],  GRID_Y['F']),
    (GRID_X['7'],  GRID_Y['E'], GRID_X['10'], GRID_Y['F']),
    (GRID_X['10'], GRID_Y['E'], GRID_X['13'], GRID_Y['F']),
    (GRID_X['13'], GRID_Y['E'], GRID_X['15'], GRID_Y['F']),
    (GRID_X['15'], GRID_Y['E'], GRID_X['17'], GRID_Y['F']),
]


def draw_slabs(m):
    set_units_tonf_m(m)

    # Conteo ANTES
    pre = verify_elements(m)
    pre_areas = pre.get('areas', 0)

    count = 0
    errors = 0

    for i, story in enumerate(STORY_NAMES):
        z = STORY_ELEVATIONS[i]

        for x1, y1, x2, y2 in SLAB_PANELS:
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

    print(f"  API reporta: {count} losas creadas ({len(SLAB_PANELS)}/piso x {len(STORY_NAMES)} pisos)")
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
    print("\n--- Dibujando losas ---")
    draw_slabs(m)
    print("\n=== 05_slabs COMPLETADO ===")


if __name__ == '__main__':
    main()
