"""
run_all.py - Script maestro del pipeline ETABS.

Version estable:
- Fase 1: geometria
- Reinicio ETABS (por defecto en --fase all)
- Fase 2: analisis
- Fase 3: post-proceso
- Fase 4: variante semi-rigida

Uso:
    cd taller-etabs
    python run_all.py
    python run_all.py --fase 1
    python run_all.py --fase 2
"""
import argparse
import importlib
import os
import sys
import time


EDB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Edificio1.edb')


def run_step(module_name, description, critical=False):
    """Ejecutar un paso del pipeline."""
    print(f"\n{'=' * 60}")
    print(f"  {description}")
    print(f"{'=' * 60}")
    t0 = time.time()
    try:
        mod = importlib.import_module(module_name)
        mod.main()
        print(f"  [{time.time() - t0:.1f}s] OK")
        return True
    except SystemExit:
        print(f"  [{time.time() - t0:.1f}s] ABORTADO")
        if critical:
            print("\n  Pipeline abortado por error critico.")
            sys.exit(1)
        return False
    except Exception as exc:
        print(f"  [ERROR] {exc}")
        import traceback
        traceback.print_exc()
        if critical:
            print("\n  Pipeline abortado por error critico.")
            sys.exit(1)
        return False


def _parse_args():
    parser = argparse.ArgumentParser(description='Pipeline ETABS completo para Edificio 1')
    parser.add_argument(
        '--fase',
        choices=['1', '2', 'all'],
        default='all',
        help='1=geometria, 2=analisis (abre Edificio1.edb), all=flujo completo estable',
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Preguntar al usuario cuando falle un paso no critico',
    )
    parser.add_argument(
        '--stop-on-noncritical',
        action='store_true',
        help='Abortar tambien cuando falle un paso no critico',
    )
    parser.add_argument(
        '--same-session',
        action='store_true',
        help='Solo para --fase all: no reiniciar ETABS entre geometria y analisis',
    )
    return parser.parse_args()


def _prepare_fase2(restart_session=False):
    """Conectar a ETABS y abrir Edificio1.edb para la fase de analisis."""
    import config_helper

    if restart_session:
        print("\n" + "~" * 60)
        print("  REINICIANDO ETABS PARA FASE 2")
        print("~" * 60)
        closed = config_helper.close_etabs(save=False)
        if not closed:
            print("  [WARN] No se pudo cerrar ETABS limpiamente. Se intentara re-adjuntar igual.")

    m = config_helper.get_model()
    ok = config_helper.open_file(m, EDB_PATH)
    if ok:
        return

    print(f"\n  [ERROR] No se pudo abrir {EDB_PATH}")
    print("  Opciones:")
    print("    1. Ejecutar primero: python run_all.py --fase 1")
    print("    2. Abrir Edificio1.edb manualmente en ETABS, luego re-correr --fase 2")
    sys.exit(1)


def _handle_noncritical_failure(module, interactive=False, stop_on_noncritical=False):
    if stop_on_noncritical:
        print(f"\n  {module} fallo y --stop-on-noncritical esta activo.")
        sys.exit(1)

    if interactive:
        resp = input(f"\n  {module} fallo. Continuar? (s/n): ").strip().lower()
        if resp != 's':
            print("Abortado.")
            sys.exit(1)
        return

    print(f"\n  [WARN] {module} fallo. Se continua en modo no interactivo para recolectar diagnostico.")


def _run_geometry(args, failed, t_total):
    print("\n" + "~" * 60)
    print("  FASE 1: GEOMETRIA")
    print("~" * 60)

    geometry_steps = [
        ('01_init_model', 'Paso 1:  Inicializar modelo y pisos', True),
        ('02_materials_sections', 'Paso 2:  Materiales y secciones', True),
        ('03_walls', 'Paso 3:  Dibujar muros', True),
        ('04_beams', 'Paso 4:  Dibujar vigas', False),
        ('05_slabs', 'Paso 5:  Dibujar losas', True),
        ('06_loads', 'Paso 6:  Patrones y cargas', False),
        ('07_diaphragm_supports', 'Paso 7:  Diafragma rigido + empotramientos', False),
        ('07b_save_checkpoint', 'Paso 7b: VERIFICACION + Checkpoint', True),
        ('07c_automesh', 'Paso 7c: Auto-Mesh muros y losas (CRITICO)', True),
    ]

    for module, desc, critical in geometry_steps:
        ok = run_step(module, desc, critical=critical)
        if ok:
            continue
        failed.append(module)
        if not critical:
            _handle_noncritical_failure(
                module,
                interactive=args.interactive,
                stop_on_noncritical=args.stop_on_noncritical,
            )

    print("\n" + "=" * 60)
    print("  FASE 1 COMPLETADA - Geometria guardada en Edificio1.edb")
    if args.fase == '1':
        print("  Siguiente paso: python run_all.py --fase 2")
    print("=" * 60)

    if args.fase == '1':
        dt = time.time() - t_total
        print(f"\n  Fase 1 completada en {dt:.0f}s.")
        if failed:
            print(f"  [WARN] Fallaron: {', '.join(failed)}")
        return False

    return True


def _run_analysis(args, failed):
    print("\n" + "~" * 60)
    print("  FASE 2: ANALISIS")
    print("~" * 60)

    analysis_steps = [
        ('08_spectrum_cases', 'Paso 8:  Espectro, modal, mass source, combos'),
        ('09_torsion_cases', 'Paso 9:  Torsion accidental'),
        ('10_save_run', 'Paso 10: Guardar + Analizar'),
    ]

    for module, desc in analysis_steps:
        ok = run_step(module, desc)
        if ok:
            continue

        failed.append(module)
        if args.stop_on_noncritical:
            print("  Geometria guardada en Edificio1.edb - completar analisis manualmente")
            sys.exit(1)
        if args.interactive:
            resp = input(f"\n  {module} fallo. Continuar? (s/n): ").strip().lower()
            if resp != 's':
                print("  Geometria guardada en Edificio1.edb - completar analisis manualmente")
                break
        else:
            print(f"  [WARN] {module} fallo. Se continua para capturar mas diagnostico.")


def _run_postprocess(failed):
    if '10_save_run' in failed:
        print("\n  [SKIP] Post-proceso saltado (analisis no corrio)")
        return

    print("\n" + "~" * 60)
    print("  FASE 3: POST-PROCESO")
    print("~" * 60)

    postprocess_steps = [
        ('11_adjust_Rstar', 'Paso 11: Leer T*, calcular R*, re-escalar'),
        ('12_results', 'Paso 12: Resumen resultados'),
    ]
    for module, desc in postprocess_steps:
        ok = run_step(module, desc)
        if not ok:
            failed.append(module)


def _run_semirigid(failed):
    if '10_save_run' in failed:
        return

    print("\n" + "~" * 60)
    print("  FASE 4: VARIANTE SEMI-RIGIDA")
    print("~" * 60)

    ok = run_step('13_semirigid', 'Paso 13: Generar variante semi-rigida')
    if not ok:
        failed.append('13_semirigid')


def main():
    args = _parse_args()

    print("=" * 60)
    print("  EDIFICIO 1 - 20 PISOS MUROS - TALLER ADSE 2026")
    print("  Generacion automatica via ETABS OAPI")
    if args.fase == '1':
        print("  Modo: FASE 1 solo (geometria)")
    elif args.fase == '2':
        print("  Modo: FASE 2 solo (analisis - abre Edificio1.edb)")
    elif args.same_session:
        print("  Modo: flujo completo legacy en una sola sesion COM")
    else:
        print("  Modo: flujo completo estable con reinicio ETABS entre fases")
    print("=" * 60)

    t_total = time.time()
    failed = []

    if args.fase in ('1', 'all'):
        should_continue = _run_geometry(args, failed, t_total)
        if not should_continue:
            return

    if args.fase == '2':
        print("\n" + "~" * 60)
        print("  ABRIENDO Edificio1.edb (sesion COM fresca)")
        print("~" * 60)
        _prepare_fase2(restart_session=False)
    elif args.fase == 'all' and not args.same_session:
        _prepare_fase2(restart_session=True)

    if args.fase in ('2', 'all'):
        _run_analysis(args, failed)
        _run_postprocess(failed)
        _run_semirigid(failed)

    dt = time.time() - t_total
    print(f"\n{'=' * 60}")
    print(f"  COMPLETADO en {dt:.0f}s ({dt / 60:.1f} min)")
    if failed:
        print(f"  [WARN] Fallaron: {', '.join(failed)}")
    else:
        print("  Todos los pasos exitosos!")
    print(f"{'=' * 60}")

    print()
    print("  ARCHIVOS GENERADOS:")
    print("  - Edificio1.edb              (diafragma rigido)")
    print("  - Edificio1_SemiRigido.edb   (sin diafragma rigido)")
    print("  - espectro_nch433.txt        (espectro para importar manual)")
    print()
    print("  VERIFICAR EN ETABS (checklist pre-entrega):")
    print("  1. Vista 3D: muros, vigas, losas visibles")
    print("  2. Malla visible en muros (View > Show Model > Auto Mesh)")
    print("  3. Peso sismico ~1 tonf/m2/piso (paso 12 lo reporta)")
    print("  4. Drift < 0.002 en CM, < 0.001 en extremos (paso 12)")
    print("  5. Qmin verificado (paso 12 lo reporta con instruccion)")
    print("  6. Mass source: PP + 1.0*TERP + 0.25*SCP")
    print("  7. P-Delta activado (MANUAL): Define > P-Delta Options")
    print()
    print("  P-DELTA (ACCION MANUAL OBLIGATORIA):")
    print("  Define > P-Delta Options > Iterative - Based on Loads")
    print("  Agregar: PP(1.0) + TERP(1.0) + TERT(1.0) + SCP(0.25)")
    print("  Luego re-analizar.")
    print()

    if failed:
        print("  PASOS MANUALES PENDIENTES:")
        if '07c_automesh' in failed:
            print("  - AUTO-MESH (CRITICO - vano min edificio = 0.425m):")
            print("    Ctrl+A -> Assign > Shell > Wall Auto Mesh Options -> MaxSize=0.4m")
            print("    Ctrl+A -> Assign > Shell > Floor Auto Mesh Options -> MaxSize=0.4m")
        if '08_spectrum_cases' in failed:
            print("  - Espectro: Define > Functions > RS > From File > espectro_nch433.txt")
            print("  - Mass source: Define > Mass Source")
        if '10_save_run' in failed:
            print("  - Analisis: Analyze > Run Analysis")
        if '11_adjust_Rstar' in failed:
            print("  - R*: Ajustar escala RS manualmente tras conocer T*")


if __name__ == '__main__':
    main()
