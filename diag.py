"""
diag.py — Diagnostico COMPLETO de conexion ETABS.
Muestra procesos, instalaciones, registro COM, y prueba cada metodo.

FIX v3: Muestra PID del proceso, verifica visibilidad, imprime archivo modelo.

USO: python diag.py
"""
import subprocess
import sys
import os
import shutil

ETABS19_EXE = r"C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"
UNIT_NAMES = {
    8: 'kgf_m_C',
    12: 'Ton_m_C',
    14: 'kgf_cm_C',
}


def section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")


def main():
    print("DIAGNOSTICO CONEXION ETABS")
    print("=" * 55)

    # --- 1. Procesos ---
    section("1. PROCESOS ETABS")
    try:
        r = subprocess.run(
            ['powershell', '-Command',
             'Get-Process ETABS -EA SilentlyContinue | '
             'Select-Object Id,Path | Format-Table -AutoSize'],
            capture_output=True, text=True, timeout=10
        )
        out = r.stdout.strip()
        print(out if out else "  (ninguno corriendo)")
    except Exception as e:
        print(f"  Error: {e}")

    # --- 2. Instalaciones ---
    section("2. INSTALACIONES")
    print(f"  ETABS 19: {'SI' if os.path.exists(ETABS19_EXE) else 'NO'}")

    d = os.path.dirname(ETABS19_EXE)
    if os.path.exists(d):
        tlbs = [f for f in os.listdir(d) if f.lower().endswith('.tlb')]
        if tlbs:
            print(f"  v19 TLBs: {', '.join(tlbs)}")

    # --- 3. Python ---
    section("3. PYTHON")
    print(f"  Python: {sys.executable}")
    print(f"  Version: {sys.version.split()[0]}")
    print(f"  Arch: {'64' if sys.maxsize > 2**32 else '32'}-bit")

    try:
        import comtypes
        gen_path = os.path.join(os.path.dirname(comtypes.__file__), 'gen')
        if os.path.exists(gen_path):
            gen_files = [f for f in os.listdir(gen_path)
                         if not f.startswith('__') and f != '__pycache__']
            print(f"  comtypes: instalado")
            print(f"  comtypes/gen: {len(gen_files)} archivos cached")
        else:
            print(f"  comtypes: instalado (gen/ vacio, se creara al conectar)")
    except ImportError:
        print("  [ERROR] comtypes NO instalado: pip install comtypes")
        return

    # --- 4. Registry COM ---
    section("4. REGISTRO COM")
    for progid in ['CSI.ETABS.API.ETABSObject', 'ETABSv1.Helper']:
        try:
            r = subprocess.run(
                ['reg', 'query', f'HKCR\\{progid}\\CLSID', '/ve'],
                capture_output=True, text=True, timeout=5
            )
            if r.returncode == 0:
                clsid = r.stdout.strip().split()[-1]
                print(f"  {progid}: {clsid}")
                r2 = subprocess.run(
                    ['reg', 'query', f'HKCR\\CLSID\\{clsid}\\LocalServer32', '/ve'],
                    capture_output=True, text=True, timeout=5
                )
                if r2.returncode == 0:
                    server = r2.stdout.strip().split('REG_SZ')[-1].strip()
                    print(f"    Server: {server}")
                    # Verificar si apunta a v19 o v21
                    if '21' in server:
                        print(f"    [WARN] Registrado como v21 — puede causar conflicto con v19")
            else:
                print(f"  {progid}: NO REGISTRADO")
        except Exception as e:
            print(f"  {progid}: Error {e}")

    # --- 5. Limpiar cache comtypes ---
    section("5. LIMPIAR CACHE COMTYPES")
    try:
        gen_path = os.path.join(os.path.dirname(comtypes.__file__), 'gen')
        cleaned = 0
        for f in os.listdir(gen_path):
            if f in ('__init__.py', '__pycache__'):
                continue
            p = os.path.join(gen_path, f)
            try:
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
                cleaned += 1
            except OSError:
                pass
        print(f"  Limpiados {cleaned} archivos de comtypes/gen")
    except Exception as e:
        print(f"  Error: {e}")

    import comtypes.client

    # --- 6. Test conexion ---
    section("6. TEST CONEXION")

    results = []

    def _test_method(label, connect_func):
        """Prueba un metodo y reporta resultado."""
        try:
            refs = connect_func()
            m = refs['model']
            u = m.GetPresentUnits()

            # Verificar archivo del modelo
            try:
                fname = m.GetModelFilename()
            except Exception:
                fname = '?'

            # Verificar visibilidad
            visible = '?'
            try:
                obj = refs.get('obj')
                if obj:
                    visible = getattr(obj, 'Visible', '?')
            except Exception:
                pass

            print(f"  [{label}] OK")
            print(f"    Units={u} ({UNIT_NAMES.get(u, 'desconocida')}), File={fname or '(vacio)'}, Visible={visible}")

            results.append((label, True, refs))
            return True
        except Exception as e:
            print(f"  [{label}] FAIL — {str(e)[:80]}")
            results.append((label, False, None))
            return False

    # A. GetActiveObject
    def _try_active():
        obj = comtypes.client.GetActiveObject('CSI.ETABS.API.ETABSObject')
        m = obj.SapModel
        return {'model': m, 'obj': obj}
    _test_method('A-GetActiveObject', _try_active)

    # B. Helper.GetObject v19
    if os.path.exists(ETABS19_EXE):
        def _try_helper_v19():
            h = comtypes.client.CreateObject('ETABSv1.Helper')
            import comtypes.gen.ETABSv1 as ETABSv1
            h = h.QueryInterface(ETABSv1.cHelper)
            obj = h.GetObject(ETABS19_EXE)
            if obj is None:
                raise Exception("GetObject retorno None")
            m = obj.SapModel
            return {'model': m, 'obj': obj, 'helper': h}
        _test_method('B-Helper.GetObject(v19)', _try_helper_v19)


    # --- Resumen ---
    section("RESUMEN")
    ok_methods = [label for label, ok, _ in results if ok]
    fail_methods = [label for label, ok, _ in results if not ok]

    if ok_methods:
        print(f"  FUNCIONAN: {', '.join(ok_methods)}")
    if fail_methods:
        print(f"  FALLAN:    {', '.join(fail_methods)}")

    # Advertencia si GetActiveObject falla
    if 'A-GetActiveObject' in fail_methods:
        print("\n  [WARN] GetActiveObject falla.")
        print("  ETABS 19 no esta en el Running Object Table.")
        print("  Soluciones:")
        print("  1. Abrir ETABS 19 manualmente, esperar 20s, reintentar")
        print("  2. Registrar ETABS 19 como admin:")
        print(f'     "{ETABS19_EXE}" /regserver')

    if not ok_methods:
        print("\n  NADA FUNCIONO. Probar:")
        print("  1. Cerrar TODO ETABS (taskkill /F /IM ETABS.exe)")
        print("  2. Abrir SOLO ETABS 19, esperar 20+ segundos")
        print("  3. python diag.py")
        print(f"\n  Si sigue fallando, registrar v19 como admin:")
        print(f'  "{ETABS19_EXE}" /regserver')
    else:
        recommended = ok_methods[0]
        print(f"\n  config_helper.py usara: {recommended}")
        print("  Puedes correr: python run_all.py")


if __name__ == '__main__':
    main()
