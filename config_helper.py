"""
config_helper.py — Conexion a ETABS 19.
IMPORTANTE: Antes de correr, asegurar que SOLO ETABS 19 este abierto.
"""
import comtypes.client
import sys

_model = None

TONF_M_C = 9
KGF_M_C = 6
KGF_CM_C = 7


def get_model():
    global _model
    if _model is not None:
        return _model

    try:
        obj = comtypes.client.CreateObject('CSI.ETABS.API.ETABSObject')
        _model = obj.SapModel
        _model.SetPresentUnits(TONF_M_C)
        print("[OK] Conectado a ETABS (tonf_m_C)")
        return _model
    except Exception as e:
        print(f"[ERROR] No se pudo conectar: {e}")
        print("Asegurate de tener SOLO ETABS 19 abierto.")
        sys.exit(1)


def set_units_kgf_cm(m):
    m.SetPresentUnits(KGF_CM_C)

def set_units_tonf_m(m):
    m.SetPresentUnits(TONF_M_C)
