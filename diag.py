"""
diag.py — Diagnostico completo de conexion ETABS.
Corre esto PRIMERO para saber que metodo funciona en tu PC.

USO: python diag.py
"""
import subprocess
import sys
import os
import time

ETABS19_EXE = r"C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"
ETABS21_EXE = r"C:\Program Files\Computers and Structures\ETABS 21\ETABS.exe"


def section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def main():
    print("DIAGNOSTICO CONEXION ETABS")
    print("="*50)

    # --- 1. Procesos ---
    section("1. PROCESOS ETABS")
    try:
        r = subprocess.run(
            ['powershell', '-Command',
             'Get-Process ETABS -EA SilentlyContinue | Select-Object Id,Path | Format-Table -AutoSize'],
            capture_output=True, text=True, timeout=10
        )
        out = r.stdout.strip()
        if out:
            print(out)
        else:
            print("  Ningun proceso ETABS corriendo")
    except Exception as e:
        print(f"  Error: {e}")

    # --- 2. Instalaciones ---
    section("2. INSTALACIONES")
    print(f"  ETABS 19: {'SI' if os.path.exists(ETABS19_EXE) else 'NO'} ({ETABS19_EXE})")
    print(f"  ETABS 21: {'SI' if os.path.exists(ETABS21_EXE) else 'NO'} ({ETABS21_EXE})")

    # TLB files
    for ver, exe in [('19', ETABS19_EXE), ('21', ETABS21_EXE)]:
        d = os.path.dirname(exe)
        if os.path.exists(d):
            tlbs = [f for f in os.listdir(d) if f.lower().endswith('.tlb')]
            if tlbs:
                print(f"  v{ver} TLBs: {', '.join(tlbs)}")

    # --- 3. Python + comtypes ---
    section("3. PYTHON")
    print(f"  Python: {sys.executable} ({sys.version.split()[0]})")
    print(f"  Arch: {8 * (8 if sys.maxsize > 2**32 else 4)}-bit")
    try:
        import comtypes
        gen_path = os.path.join(os.path.dirname(comtypes.__file__), 'gen')
        gen_files = [f for f in os.listdir(gen_path) if not f.startswith('__')]
        print(f"  comtypes: {comtypes.__version__ if hasattr(comtypes, '__version__') else 'instalado'}")
        print(f"  comtypes/gen: {len(gen_files)} archivos cached")
        if gen_files:
            print(f"    {', '.join(gen_files[:5])}{'...' if len(gen_files)>5 else ''}")
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
            clsid = r.stdout.strip().split()[-1] if r.returncode == 0 else 'NO ENCONTRADO'
            print(f"  {progid}: {clsid}")

            if r.returncode == 0 and clsid != 'NO ENCONTRADO':
                # Buscar LocalServer32
                r2 = subprocess.run(
                    ['reg', 'query', f'HKCR\\CLSID\\{clsid}\\LocalServer32', '/ve'],
                    capture_output=True, text=True, timeout=5
                )
                if r2.returncode == 0:
                    server = r2.stdout.strip().split('REG_SZ')[-1].strip()
                    print(f"    Server: {server}")
        except Exception as e:
            print(f"  {progid}: Error {e}")

    # --- 5. Test conexion ---
    section("5. TEST CONEXION")
    import comtypes.client

    # Metodo A: Helper.GetObject (CORRECTO para dual-install)
    print("\n  [A] Helper.GetObject(ETABS19_EXE):")
    try:
        helper = comtypes.client.CreateObject('ETABSv1.Helper')
        import comtypes.gen.ETABSv1 as ETABSv1
        helper = helper.QueryInterface(ETABSv1.cHelper)
        obj = helper.GetObject(ETABS19_EXE)
        m = obj.SapModel
        u = m.GetPresentUnits()
        print(f"      [OK] Unidades={u}")
        m.SetPresentUnits(9)
        print(f"      [OK] SetPresentUnits(9) OK")
        try:
            ret = m.InitializeNewModel(9)
            print(f"      [OK] InitializeNewModel ret={ret}")
        except Exception as e:
            print(f"      [FAIL] InitializeNewModel: {e}")
    except Exception as e:
        print(f"      [FAIL] {e}")

    # Metodo B: GetActiveObject
    print("\n  [B] GetActiveObject:")
    try:
        obj = comtypes.client.GetActiveObject('CSI.ETABS.API.ETABSObject')
        m = obj.SapModel
        u = m.GetPresentUnits()
        print(f"      [OK] Unidades={u}")
    except Exception as e:
        print(f"      [FAIL] {e}")

    # Metodo C: CreateObject (MALO — lanza v21)
    print("\n  [C] CreateObject (lanza v21!):")
    try:
        obj = comtypes.client.CreateObject('CSI.ETABS.API.ETABSObject')
        m = obj.SapModel
        u = m.GetPresentUnits()
        print(f"      [OK] Unidades={u}")
        print("      [WARN] Esto probablemente conecto a ETABS 21, no 19")
    except Exception as e:
        print(f"      [FAIL] {e}")

    # Metodo D: Helper.CreateObject (lanza v19 nueva instancia)
    print("\n  [D] Helper.CreateObject(ETABS19_EXE) — lanza nueva instancia v19:")
    try:
        helper = comtypes.client.CreateObject('ETABSv1.Helper')
        import comtypes.gen.ETABSv1 as ETABSv1
        helper = helper.QueryInterface(ETABSv1.cHelper)
        obj = helper.CreateObject(ETABS19_EXE)
        m = obj.SapModel
        u = m.GetPresentUnits()
        print(f"      [OK] Unidades={u}")
    except Exception as e:
        print(f"      [FAIL] {e}")

    section("RESULTADO")
    print("  Si [A] funciona: perfecto, config_helper.py ya usa este metodo")
    print("  Si [A] falla pero [D] funciona: editar config_helper.py para usar CreateObject(path)")
    print("  Si solo [C] funciona: hay que desregistrar ETABS 21 o registrar v19")
    print("  Si nada funciona: limpiar comtypes\\gen\\*, reiniciar ETABS, reintentar")


if __name__ == '__main__':
    main()
