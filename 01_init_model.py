"""
01_init_model.py — Conectar a ETABS, inicializar modelo vacio, definir pisos.
"""
from config_helper import get_model
from config import N_STORIES, STORY_NAMES, STORY_HEIGHTS, STORY_ELEVATIONS


def main():
    m = get_model()

    # Inicializar modelo en blanco (9 = tonf_m_C)
    ret = m.InitializeNewModel(9)
    print(f"  InitializeNewModel: ret={ret}")
    ret = m.File.NewBlank()
    print(f"  File.NewBlank: ret={ret}")

    # Definir pisos — probar multiples firmas porque v19 y v21 difieren
    elevations = [0.0] + STORY_ELEVATIONS  # N+1 elementos

    # Firma A: v16/v19 — SetStories(Names, Elevations, Heights, Master, Similar, Splice, SpliceH)
    try:
        ret = m.Story.SetStories(
            STORY_NAMES,
            elevations,
            STORY_HEIGHTS,
            [True] * N_STORIES,
            [''] * N_STORIES,
            [False] * N_STORIES,
            [0.0] * N_STORIES,
        )
        print(f"  SetStories (firma A): ret={ret}")
    except Exception as e1:
        print(f"  SetStories firma A fallo: {e1}")

        # Firma B: v21 — SetStories(BaseElev, NumStories, Names, Heights, Master, Similar, Splice, SpliceH)
        try:
            ret = m.Story.SetStories(
                0.0,
                N_STORIES,
                STORY_NAMES,
                STORY_HEIGHTS,
                [True] * N_STORIES,
                [''] * N_STORIES,
                [False] * N_STORIES,
                [0.0] * N_STORIES,
            )
            print(f"  SetStories (firma B): ret={ret}")
        except Exception as e2:
            print(f"  SetStories firma B fallo: {e2}")

            # Fallback C: crear pisos uno a uno
            try:
                print("  Intentando crear pisos uno a uno...")
                elev = 0.0
                for i in range(N_STORIES):
                    elev += STORY_HEIGHTS[i]
                    try:
                        m.Story.SetStories(
                            [STORY_NAMES[i]],
                            [elev - STORY_HEIGHTS[i], elev],
                            [STORY_HEIGHTS[i]],
                            [True],
                            [''],
                            [False],
                            [0.0],
                        )
                    except Exception:
                        pass
                print(f"  Pisos creados individualmente")
                ret = 0
            except Exception as e3:
                print(f"  Fallback C fallo: {e3}")
                ret = -1

    if ret != 0:
        print("  [WARN] SetStories fallo, verificar manualmente en ETABS")
    else:
        print(f"[OK] {N_STORIES} pisos (H total = {STORY_ELEVATIONS[-1]} m)")

    print("\n=== 01_init_model COMPLETADO ===")


if __name__ == '__main__':
    main()
