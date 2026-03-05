"""
run_all.py — Script maestro. Ejecuta todos los componentes en orden.

FIX v3:
- Verificacion post-geometria (aborta si modelo vacio)
- Mejor manejo de errores (no pierde geometria por crash en analisis)
- Guardado intermedio automatico

USO: Abrir ETABS con modelo nuevo vacio, luego:
     cd taller-etabs
     python run_all.py
"""
import importlib
import sys
import time


def run_step(module_name, description, critical=False):
    """Ejecutar un paso del pipeline.

    Args:
        critical: Si True y falla, aborta el pipeline.
    """
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    t0 = time.time()
    try:
        mod = importlib.import_module(module_name)
        mod.main()
        print(f"  [{time.time()-t0:.1f}s] OK")
        return True
    except SystemExit:
        # 07b puede llamar sys.exit(1) si modelo vacio
        print(f"  [{time.time()-t0:.1f}s] ABORTADO")
        if critical:
            print("\n  Pipeline abortado por error critico.")
            sys.exit(1)
        return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()
        if critical:
            print("\n  Pipeline abortado por error critico.")
            sys.exit(1)
        return False


def main():
    print("=" * 60)
    print("  EDIFICIO 1 — 20 PISOS MUROS — TALLER ADSE 2026")
    print("  Generacion automatica via ETABS OAPI")
    print("  Pipeline completo: geometria → analisis → resultados")
    print("=" * 60)

    t_total = time.time()
    failed = []

    # ============================================================
    # FASE 1: GEOMETRIA (critica — si falla, no seguir)
    # ============================================================
    print("\n" + "~" * 60)
    print("  FASE 1: GEOMETRIA")
    print("~" * 60)

    geometry_steps = [
        ('01_init_model',         'Paso 1:  Inicializar modelo y pisos',   True),
        ('02_materials_sections', 'Paso 2:  Materiales y secciones',       True),
        ('03_walls',              'Paso 3:  Dibujar muros',                True),
        ('04_beams',              'Paso 4:  Dibujar vigas',                True),
        ('05_slabs',              'Paso 5:  Dibujar losas',                True),
        ('06_loads',              'Paso 6:  Patrones y cargas',            False),
        ('07_diaphragm_supports', 'Paso 7:  Diafragma rigido + empotramientos', False),
        ('07b_save_checkpoint',   'Paso 7b: VERIFICACION + Checkpoint',    True),
    ]

    for module, desc, critical in geometry_steps:
        ok = run_step(module, desc, critical=critical)
        if not ok:
            failed.append(module)
            if not critical:
                resp = input(f"\n  {module} fallo. Continuar? (s/n): ").strip().lower()
                if resp != 's':
                    print("Abortado.")
                    sys.exit(1)

    print("\n" + "=" * 60)
    print("  FASE 1 COMPLETADA — Geometria guardada en Edificio1.edb")
    print("=" * 60)

    # ============================================================
    # FASE 2: ANALISIS (no critica — si falla, modelo no se pierde)
    # ============================================================
    print("\n" + "~" * 60)
    print("  FASE 2: ANALISIS")
    print("~" * 60)

    analysis_steps = [
        ('08_spectrum_cases',     'Paso 8:  Espectro, modal, mass source, combos'),
        ('09_torsion_cases',      'Paso 9:  Torsion accidental'),
        ('10_save_run',           'Paso 10: Guardar + Analizar'),
    ]

    for module, desc in analysis_steps:
        ok = run_step(module, desc)
        if not ok:
            failed.append(module)
            resp = input(f"\n  {module} fallo. Continuar? (s/n): ").strip().lower()
            if resp != 's':
                print(f"  Geometria guardada en Edificio1.edb — completar analisis manualmente")
                break

    # ============================================================
    # FASE 3: POST-PROCESO
    # ============================================================
    if '10_save_run' not in failed:
        print("\n" + "~" * 60)
        print("  FASE 3: POST-PROCESO")
        print("~" * 60)

        postprocess_steps = [
            ('11_adjust_Rstar', 'Paso 11: Leer T*, calcular R*, re-escalar'),
            ('12_results',      'Paso 12: Resumen resultados'),
        ]

        for module, desc in postprocess_steps:
            ok = run_step(module, desc)
            if not ok:
                failed.append(module)
    else:
        print("\n  [SKIP] Post-proceso saltado (analisis no corrio)")

    # ============================================================
    # FASE 4: VARIANTE SEMI-RIGIDA
    # ============================================================
    if '10_save_run' not in failed:
        print("\n" + "~" * 60)
        print("  FASE 4: VARIANTE SEMI-RIGIDA")
        print("~" * 60)

        ok = run_step('13_semirigid', 'Paso 13: Generar variante semi-rigida')
        if not ok:
            failed.append('13_semirigid')

    # ============================================================
    # RESUMEN
    # ============================================================
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
    print("  - Edificio1.edb              (diafragma rigido)")
    print("  - Edificio1_SemiRigido.edb   (sin diafragma rigido)")
    print("  - espectro_nch433.txt        (espectro para importar manual)")
    print()
    print("  VERIFICAR EN ETABS:")
    print("  1. Vista 3D: muros, vigas, losas visibles")
    print("  2. Peso sismico ~1 tonf/m2/piso")
    print("  3. Drift < 0.002 en CM")
    print("  4. Mass source: PP + 1.0*TERP + 0.25*SCP")
    print()
    if failed:
        print("  PASOS MANUALES PENDIENTES:")
        if '08_spectrum_cases' in failed:
            print("  - Espectro: Define > Functions > RS > From File > espectro_nch433.txt")
            print("  - Mass source: Define > Mass Source")
        if '10_save_run' in failed:
            print("  - Analisis: Analyze > Run Analysis")
        if '11_adjust_Rstar' in failed:
            print("  - R*: Ajustar escala RS manualmente tras conocer T*")


if __name__ == '__main__':
    main()
