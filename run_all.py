"""
run_all.py — Script maestro. Ejecuta todos los componentes en orden.
USO: Abrir ETABS con modelo nuevo vacio, luego:
     cd taller-etabs
     python run_all.py
"""
import importlib
import sys
import time


def run_step(module_name, description):
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    t0 = time.time()
    try:
        mod = importlib.import_module(module_name)
        mod.main()
        print(f"  [{time.time()-t0:.1f}s] OK")
        return True
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("  EDIFICIO 1 — 20 PISOS MUROS — TALLER ADSE 2026")
    print("  Generacion automatica via ETABS OAPI")
    print("=" * 60)

    # Nota: nombres sin extension .py
    steps = [
        ('01_init_model',         'Paso 1: Inicializar modelo y pisos'),
        ('02_materials_sections', 'Paso 2: Materiales y secciones'),
        ('03_walls',              'Paso 3: Dibujar muros'),
        ('04_beams',              'Paso 4: Dibujar vigas'),
        ('05_slabs',              'Paso 5: Dibujar losas'),
        ('06_loads',              'Paso 6: Patrones y cargas'),
        ('07_diaphragm_supports', 'Paso 7: Diafragma + empotramientos'),
        ('08_spectrum_cases',     'Paso 8: Espectro, modal, RS, combos'),
    ]

    t_total = time.time()
    failed = []

    for module, desc in steps:
        ok = run_step(module, desc)
        if not ok:
            failed.append(module)
            resp = input(f"\n  {module} fallo. Continuar? (s/n): ").strip().lower()
            if resp != 's':
                print("Abortado.")
                sys.exit(1)

    dt = time.time() - t_total
    print(f"\n{'='*60}")
    print(f"  COMPLETADO en {dt:.1f}s")
    if failed:
        print(f"  [WARN] Fallaron: {', '.join(failed)}")
    else:
        print("  Todos los pasos exitosos!")
    print(f"{'='*60}")
    print()
    print("  SIGUIENTE:")
    print("  1. Verificar modelo en vista 3D")
    print("  2. Verificar peso sismico (~1 tonf/m2)")
    print("  3. Ajustar R* segun T* (tras primer Run Analysis)")
    print("  4. Run Analysis")


if __name__ == '__main__':
    main()
