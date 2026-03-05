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
    print("  Pipeline completo: geometria → analisis → resultados")
    print("=" * 60)

    # Nota: nombres sin extension .py
    steps = [
        # FASE 1: GEOMETRIA
        ('01_init_model',         'Paso 1:  Inicializar modelo y pisos'),
        ('02_materials_sections', 'Paso 2:  Materiales y secciones'),
        ('03_walls',              'Paso 3:  Dibujar muros'),
        ('04_beams',              'Paso 4:  Dibujar vigas'),
        ('05_slabs',              'Paso 5:  Dibujar losas'),
        ('06_loads',              'Paso 6:  Patrones y cargas'),
        ('07_diaphragm_supports', 'Paso 7:  Diafragma rigido + empotramientos'),
        # FASE 2: ANALISIS
        ('08_spectrum_cases',     'Paso 8:  Espectro, modal, mass source, combos'),
        ('09_torsion_cases',      'Paso 9:  Torsion accidental (caso a + b forma 2)'),
        ('10_save_run',           'Paso 10: Guardar + Analizar (espectro elastico)'),
        # FASE 3: POST-PROCESO
        ('11_adjust_Rstar',       'Paso 11: Leer T*, calcular R*, re-escalar, re-analizar'),
        ('12_results',            'Paso 12: Resumen resultados'),
        # FASE 4: VARIANTE
        ('13_semirigid',          'Paso 13: Generar variante semi-rigida'),
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
    print(f"  COMPLETADO en {dt:.0f}s ({dt/60:.1f} min)")
    if failed:
        print(f"  [WARN] Fallaron: {', '.join(failed)}")
    else:
        print("  Todos los pasos exitosos!")
    print(f"{'='*60}")

    print()
    print("  ARCHIVOS GENERADOS:")
    print("  - Edificio1.edb         (diafragma rigido, con R*)")
    print("  - Edificio1_SemiRigido.edb (sin diafragma rigido)")
    print("  - espectro_nch433.txt   (espectro para importar manual)")
    print()
    print("  VERIFICAR EN ETABS:")
    print("  1. Vista 3D: muros, vigas, losas visibles")
    print("  2. Peso sismico ~1 tonf/m2/piso")
    print("  3. Drift < 0.002 en CM (condicion 1 NCh433)")
    print("  4. Mass source: PP + 1.0*TERP + 0.25*SCP")
    print()
    print("  PASOS MANUALES (si falló algo):")
    print("  - Espectro: Define > Functions > RS > From File > espectro_nch433.txt")
    print("  - Mass source: Define > Mass Source")
    print("  - Torsion caso b) forma 1: ver LEEME.md")


if __name__ == '__main__':
    main()
