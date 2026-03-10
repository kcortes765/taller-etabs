"""
diag.py - Diagnostico de conexion ETABS.

Muestra:
- procesos ETABS
- instalacion y registro COM
- estado de Python/comtypes
- prueba de GetActiveObject

Diseno intencionalmente seguro:
- no crea modelos
- no lanza ETABS via COM
- no usa Helper.GetObject(exe_path), porque CSI documenta GetObject(typeName),
  no una ruta al ejecutable
"""
import os
import shutil
import subprocess
import sys


ETABS19_EXE = r"C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"
UNIT_NAMES = {
    8: 'kgf_m_C',
    12: 'Ton_m_C',
    14: 'kgf_cm_C',
}


def section(title):
    print(f"\n{'=' * 55}")
    print(f"  {title}")
    print(f"{'=' * 55}")


def _print_registry_info(progid):
    try:
        result = subprocess.run(
            ['reg', 'query', f'HKCR\\{progid}\\CLSID', '/ve'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            print(f"  {progid}: NO REGISTRADO")
            return

        clsid = result.stdout.strip().split()[-1]
        print(f"  {progid}: {clsid}")

        server = subprocess.run(
            ['reg', 'query', f'HKCR\\CLSID\\{clsid}\\LocalServer32', '/ve'],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if server.returncode == 0:
            exe = server.stdout.strip().split('REG_SZ')[-1].strip()
            print(f"    Server: {exe}")
            if 'ETABS 21' in exe or '\\21\\' in exe or ' 21\\' in exe:
                print("    [WARN] Registro COM parece apuntar a ETABS 21")
    except Exception as exc:
        print(f"  {progid}: Error {exc}")


def main():
    print("DIAGNOSTICO CONEXION ETABS")
    print("=" * 55)

    section("1. PROCESOS ETABS")
    try:
        result = subprocess.run(
            [
                'powershell',
                '-Command',
                'Get-Process ETABS -EA SilentlyContinue | '
                'Select-Object Id,Path | Format-Table -AutoSize',
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout.strip()
        print(output if output else "  (ninguno corriendo)")
    except Exception as exc:
        print(f"  Error: {exc}")

    section("2. INSTALACIONES")
    print(f"  ETABS 19: {'SI' if os.path.exists(ETABS19_EXE) else 'NO'}")
    install_dir = os.path.dirname(ETABS19_EXE)
    if os.path.exists(install_dir):
        tlbs = [f for f in os.listdir(install_dir) if f.lower().endswith('.tlb')]
        if tlbs:
            print(f"  TLBs: {', '.join(tlbs)}")

    section("3. PYTHON")
    print(f"  Python: {sys.executable}")
    print(f"  Version: {sys.version.split()[0]}")
    print(f"  Arch: {'64' if sys.maxsize > 2**32 else '32'}-bit")

    try:
        import comtypes
    except ImportError:
        print("  [ERROR] comtypes NO instalado: pip install comtypes")
        return

    gen_path = os.path.join(os.path.dirname(comtypes.__file__), 'gen')
    if os.path.exists(gen_path):
        gen_files = [f for f in os.listdir(gen_path) if not f.startswith('__') and f != '__pycache__']
        print("  comtypes: instalado")
        print(f"  comtypes/gen: {len(gen_files)} archivos cached")
    else:
        print("  comtypes: instalado (gen/ vacio)")

    section("4. REGISTRO COM")
    for progid in ['CSI.ETABS.API.ETABSObject', 'ETABSv1.Helper']:
        _print_registry_info(progid)

    section("5. LIMPIAR CACHE COMTYPES")
    try:
        cleaned = 0
        if os.path.exists(gen_path):
            for entry in os.listdir(gen_path):
                if entry in ('__init__.py', '__pycache__'):
                    continue
                path = os.path.join(gen_path, entry)
                try:
                    shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
                    cleaned += 1
                except OSError:
                    pass
        print(f"  Limpiados {cleaned} archivos de comtypes/gen")
    except Exception as exc:
        print(f"  Error: {exc}")

    import comtypes.client

    section("6. TEST CONEXION")
    results = []

    def _test_method(label, connect_func):
        try:
            refs = connect_func()
            model = refs['model']
            units = model.GetPresentUnits()
            try:
                filename = model.GetModelFilename()
            except Exception:
                filename = '?'
            visible = '?'
            try:
                obj = refs.get('obj')
                if obj is not None:
                    visible = getattr(obj, 'Visible', '?')
            except Exception:
                pass

            print(f"  [{label}] OK")
            print(f"    Units={units} ({UNIT_NAMES.get(units, 'desconocida')}), File={filename or '(vacio)'}, Visible={visible}")
            results.append((label, True))
            return True
        except Exception as exc:
            print(f"  [{label}] FAIL - {str(exc)[:80]}")
            results.append((label, False))
            return False

    def _try_active():
        obj = comtypes.client.GetActiveObject('CSI.ETABS.API.ETABSObject')
        return {'obj': obj, 'model': obj.SapModel}

    _test_method('A-GetActiveObject', _try_active)

    print("  [INFO] Helper.GetObject(exe_path) omitido: la API oficial documenta GetObject(typeName), no ruta .exe.")
    print("  [INFO] config_helper.py usa GetActiveObject + autostart visible de ETABS 19.")

    section("RESUMEN")
    ok_methods = [label for label, ok in results if ok]
    fail_methods = [label for label, ok in results if not ok]

    if ok_methods:
        print(f"  FUNCIONAN: {', '.join(ok_methods)}")
    if fail_methods:
        print(f"  FALLAN:    {', '.join(fail_methods)}")

    if 'A-GetActiveObject' in fail_methods:
        print("\n  [WARN] GetActiveObject falla.")
        print("  ETABS 19 no esta en el Running Object Table.")
        print("  Soluciones:")
        print("  1. Abrir ETABS 19 manualmente y esperar 20-30s")
        print("  2. Repetir: python diag.py")
        print("  3. Si sigue fallando, registrar ETABS 19 como admin:")
        print(f'     "{ETABS19_EXE}" /regserver')
    else:
        print("\n  Puedes correr: python run_all.py")


if __name__ == '__main__':
    main()
