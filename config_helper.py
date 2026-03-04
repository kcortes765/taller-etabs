"""
config_helper.py — Conexion a ETABS 19 especificamente.
"""
import comtypes.client
import sys

_model = None

TONF_M_C = 9
KGF_M_C = 6
KGF_CM_C = 7

ETABS19_PATH = r"C:\Program Files\Computers and Structures\ETABS 19\ETABS.exe"


def get_model():
    """Conectar al ETABS 19 que esta corriendo."""
    global _model
    if _model is not None:
        return _model

    # Usar Helper.GetObject con la ruta exacta de ETABS 19
    try:
        helper = comtypes.client.CreateObject('ETABSv1.Helper')
        # QueryInterface para acceder a GetObject
        try:
            import comtypes.gen.ETABSv1 as ETABSv1
            helper = helper.QueryInterface(ETABSv1.cHelper)
        except Exception:
            pass
        obj = helper.GetObject(ETABS19_PATH)
        _model = obj.SapModel
        _model.SetPresentUnits(TONF_M_C)
        print("[OK] Conectado a ETABS 19 via Helper.GetObject")
        return _model
    except Exception as e:
        print(f"  Helper.GetObject: {e}")

    # Fallback: GetActiveObject
    try:
        obj = comtypes.client.GetActiveObject('CSI.ETABS.API.ETABSObject')
        _model = obj.SapModel
        _model.SetPresentUnits(TONF_M_C)
        print("[OK] Conectado via GetActiveObject")
        return _model
    except Exception as e:
        print(f"  GetActiveObject: {e}")

    print("[ERROR] No se pudo conectar a ETABS 19.")
    print(f"  Verifica que ETABS 19 este abierto: {ETABS19_PATH}")
    sys.exit(1)


def set_units_kgf_cm(m):
    m.SetPresentUnits(KGF_CM_C)

def set_units_tonf_m(m):
    m.SetPresentUnits(TONF_M_C)
