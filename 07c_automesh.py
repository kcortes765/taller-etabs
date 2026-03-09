"""
07c_automesh.py — Aplicar Auto-Mesh a muros y losas via OAPI.

CRITICO: Sin mallado, los resultados son INVALIDOS para entrega:
  - Sin mesh: T* ~ 0.2s (irreal), drift ~ 0.0001 (irreal)
  - Con mesh: T* ~ 1.0-1.5s (real), drift < 0.002 (verificable)

Intenta malla de 1.0m via API. Si falla, da instrucciones manuales exactas.
"""
from config_helper import get_model, set_units_tonf_m, unlock_model, verify_elements

# Tamano maximo de elemento (m)
# CRITICO: vano minimo del edificio es 0.425m (ejes 8-9).
# Con 1.0m → esos paneles quedan 100% reducidos (sin masa ni rigidez).
# Con 0.4m → 2 elementos de 0.213m entran en el vano minimo. OK.
MAX_MESH_SIZE = 0.4


def apply_automesh_to_areas(m):
    """Intentar aplicar AutoMesh a todos los area objects (muros + losas).

    Retorna (ok_count, fail_count, total_count).
    """
    # Obtener lista de areas
    try:
        result = m.AreaObj.GetNameList()
        # Formato: (NumberItems, [Names], ret)
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            names_raw = result[1] if len(result) > 1 else []
            if isinstance(names_raw, (list, tuple)):
                names = list(names_raw)
            else:
                names = []
        else:
            names = []
    except Exception as e:
        print(f"  [WARN] GetNameList: {e}")
        return 0, 0, 0

    total = len(names)
    if total == 0:
        print("  [WARN] No hay area objects en el modelo.")
        return 0, 0, 0

    print(f"  Aplicando AutoMesh a {total} areas (max {MAX_MESH_SIZE}m)...")

    ok = 0
    fail = 0
    last_err = None

    # Firmas conocidas de SetAutoMesh (ETABS v19/v21):
    # MeshType: 0=None, 1=N puntos, 2=MaxSize, 3=Match joints
    # Firma completa: (Name, MeshType, N1, N2, MaxSize1, MaxSize2,
    #                  PointOnEdgesFromLines, PointOnEdgesFromPoints,
    #                  ExtendCoordLines, MatchCoordLines)
    def _try_mesh(name):
        attempts = [
            # Firma completa v19
            lambda n: m.AreaObj.SetAutoMesh(
                n, 2, 0, 0,
                MAX_MESH_SIZE, MAX_MESH_SIZE,
                True, True, False, False),
            # Sin los ultimos dos booleanos
            lambda n: m.AreaObj.SetAutoMesh(
                n, 2, 0, 0,
                MAX_MESH_SIZE, MAX_MESH_SIZE,
                True, True),
            # Solo tipo y tamano
            lambda n: m.AreaObj.SetAutoMesh(
                n, 2, MAX_MESH_SIZE, MAX_MESH_SIZE),
            # Con ret explicito al final
            lambda n: m.AreaObj.SetAutoMesh(
                n, 2, 0, 0,
                MAX_MESH_SIZE, MAX_MESH_SIZE,
                True, True, False, False, 0),
        ]
        for func in attempts:
            try:
                ret = func(name)
                # ret puede ser int o tuple; cualquier cosa sin excepcion es OK
                return True, None
            except AttributeError:
                return False, "SetAutoMesh no existe en esta version"
            except Exception as e:
                last = str(e)
                continue
        return False, last

    # Probar con el primer elemento para ver si la API existe
    if names:
        ok_test, err_test = _try_mesh(names[0])
        if not ok_test and "no existe" in str(err_test):
            print(f"  [INFO] SetAutoMesh no disponible en esta version: {err_test}")
            return 0, total, total

    # Aplicar a todos
    for name in names:
        ok_flag, err = _try_mesh(name)
        if ok_flag:
            ok += 1
        else:
            fail += 1
            last_err = err

    return ok, fail, total


def main():
    m = get_model()
    unlock_model(m)
    set_units_tonf_m(m)

    print("\n=== 07c_automesh: Auto-Mesh de muros y losas ===")
    print(f"  Tamano de malla objetivo: {MAX_MESH_SIZE}m")
    print("  (Sin malla: T* y drifts son IRREALES en modelos de muros)")

    # Verificar que hay elementos
    counts = verify_elements(m)
    areas = counts.get('areas', 0)
    if areas == 0:
        print("  [ERROR] No hay areas en el modelo. Ejecutar pasos 3-5 primero.")
        return

    print(f"\n  Areas encontradas: {areas}")

    ok, fail, total = apply_automesh_to_areas(m)

    if ok > 0:
        print(f"\n  [OK] AutoMesh aplicado: {ok}/{total} areas")
        if fail > 0:
            print(f"  [WARN] Fallaron: {fail} areas")
        print(f"\n  Verificar en ETABS:")
        print(f"    View > Show Model → activar 'Show Auto Mesh'")
        print(f"    Deberian verse cuadriculas de ~{MAX_MESH_SIZE}m en los muros")
    else:
        print(f"\n  [WARN] AutoMesh via API no funciono ({fail} areas).")
        _print_manual_instructions()

    print("\n=== 07c_automesh COMPLETADO ===")
    print("  IMPORTANTE: Verificar malla manualmente antes de analizar (ver instrucciones)")


def _print_manual_instructions():
    """Imprimir instrucciones detalladas para aplicar AutoMesh manualmente."""
    print()
    print("  " + "=" * 56)
    print("  INSTRUCCION MANUAL — OBLIGATORIA ANTES DE ANALIZAR")
    print("  " + "=" * 56)
    print()
    print("  1. En ETABS: Ctrl+A  (seleccionar todo)")
    print()
    print("  2. MUROS:")
    print("     Assign > Shell > Wall Auto Mesh Options")
    print("     ┌─────────────────────────────────────────┐")
    print("     │ ☑ Auto Rectangular Mesh                 │")
    print("     │   Max Element Size: 0.4  m              │")
    print("     │ ☑ Add Restraint Points from Lines       │")
    print("     │ ☑ Add Restraint Points from Points      │")
    print("     └─────────────────────────────────────────┘")
    print("     → OK")
    print()
    print("  3. LOSAS:")
    print("     Assign > Shell > Floor Auto Mesh Options")
    print("     ┌─────────────────────────────────────────┐")
    print("     │ ☑ Auto Rectangular Mesh                 │")
    print("     │   Max Element Size: 0.4  m              │")
    print("     │ ☑ Add Restraint Points from Lines       │")
    print("     └─────────────────────────────────────────┘")
    print("     → OK")
    print()
    print("  4. File > Save (guardar antes de analizar)")
    print()
    print("  POR QUE ES CRITICO:")
    print("    Sin malla → ETABS usa 1 elemento por piso → T* ~ 0.2s (irreal)")
    print("    Con malla → T* ~ 1.0-1.5s (realista para 20p muros HA)")
    print("    Sin malla → drift ~ 0.00001 (irreal, modelo muy rigido)")
    print("    Con malla → drift verifiable con NCh433 limite 0.002")
    print("  " + "=" * 56)


if __name__ == '__main__':
    main()
