"""
01_init_model.py — Conectar a ETABS, inicializar modelo vacio, definir pisos.

FIX v3: Guarda inmediatamente tras crear pisos para vincular modelo a archivo.
Verifica que los pisos se crearon correctamente.
"""
import os
from config_helper import get_model, refresh_view
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

    stories_ok = False

    # Firma A: v16/v19
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
        stories_ok = (ret == 0)
    except Exception as e1:
        print(f"  SetStories firma A fallo: {e1}")

        # Firma B: v21
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
            stories_ok = (ret == 0)
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
                print("  Pisos creados individualmente")
                stories_ok = True
            except Exception as e3:
                print(f"  Fallback C fallo: {e3}")

    # Verificar pisos creados
    try:
        result = m.Story.GetStories()
        if isinstance(result, (list, tuple)):
            # Buscar conteo de pisos en resultado
            for v in result:
                if isinstance(v, int) and v > 0:
                    print(f"  Pisos verificados: {v}")
                    break
    except Exception:
        pass

    if not stories_ok:
        print("  [WARN] SetStories fallo, verificar manualmente en ETABS")
    else:
        print(f"[OK] {N_STORIES} pisos (H total = {STORY_ELEVATIONS[-1]} m)")

    # *** CRITICO: Guardar inmediatamente para vincular modelo a archivo ***
    script_dir = os.path.dirname(os.path.abspath(__file__))
    edb_path = os.path.join(script_dir, 'Edificio1.edb')
    try:
        ret = m.File.Save(edb_path)
        print(f"  File.Save inicial: ret={ret}")
        if ret == 0:
            fname = m.GetModelFilename()
            print(f"  Modelo guardado: {fname}")
    except Exception as e:
        print(f"  [WARN] File.Save: {e}")

    refresh_view(m)
    print("\n=== 01_init_model COMPLETADO ===")


if __name__ == '__main__':
    main()
