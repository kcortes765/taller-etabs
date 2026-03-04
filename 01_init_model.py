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

    # Definir pisos
    # SetStories(StoryNames, StoryElevations, StoryHeights,
    #            IsMasterStory, SimilarToStory, SpliceAbove, SpliceHeight)
    # StoryElevations tiene N+1 elementos: [base, piso1_top, piso2_top, ...]
    elevations = [0.0] + STORY_ELEVATIONS  # N+1 elementos

    ret = m.Story.SetStories(
        STORY_NAMES,                    # StoryNames (N)
        elevations,                     # StoryElevations (N+1)
        STORY_HEIGHTS,                  # StoryHeights (N)
        [True] * N_STORIES,             # IsMasterStory (N)
        [''] * N_STORIES,               # SimilarToStory (N)
        [False] * N_STORIES,            # SpliceAbove (N)
        [0.0] * N_STORIES,              # SpliceHeight (N)
    )
    print(f"  SetStories: ret={ret}")

    if ret != 0:
        print("  [WARN] SetStories fallo, verificar manualmente en ETABS")

    print(f"[OK] {N_STORIES} pisos (H total = {STORY_ELEVATIONS[-1]} m)")
    print("\n=== 01_init_model COMPLETADO ===")


if __name__ == '__main__':
    main()
