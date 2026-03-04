"""
config_helper.py — Conexion a ETABS compartida entre todos los scripts.
Requiere ETABS abierto con un modelo (o vacio para crear uno nuevo).
"""
import comtypes.client
import sys

_model = None

TONF_M_C = 9
KGF_M_C = 6
KGF_CM_C = 7


def get_model():
    """Conectar a ETABS abierto y retornar SapModel."""
    global _model
    if _model is not None:
        return _model

    # Metodo 1: Conectar al ETABS que ya esta corriendo
    try:
        obj = comtypes.client.GetActiveObject('CSI.ETABS.API.ETABSObject')
        _model = obj.SapModel
        _model.SetPresentUnits(TONF_M_C)
        print("[OK] Conectado a ETABS existente (GetActiveObject)")
        return _model
    except Exception:
        pass

    # Metodo 2: Crear instancia nueva
    try:
        helper = comtypes.client.CreateObject('ETABSv1.Helper')
        obj = helper.CreateObjectProgID('CSI.ETABS.API.ETABSObject')
        obj.ApplicationStart()
        _model = obj.SapModel
        _model.SetPresentUnits(TONF_M_C)
        print("[OK] Conectado a ETABS (nueva instancia via Helper)")
        return _model
    except Exception:
        pass

    # Metodo 3: CreateObject directo (fallback)
    try:
        obj = comtypes.client.CreateObject('CSI.ETABS.API.ETABSObject')
        _model = obj.SapModel
        _model.SetPresentUnits(TONF_M_C)
        print("[OK] Conectado a ETABS (CreateObject)")
        return _model
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a ETABS: {e}")
        print("Asegurate de tener ETABS abierto.")
        sys.exit(1)


def set_units_kgf_cm(m):
    m.SetPresentUnits(KGF_CM_C)

def set_units_tonf_m(m):
    m.SetPresentUnits(TONF_M_C)
