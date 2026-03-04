"""
config_helper.py — Conexion a ETABS compartida entre todos los scripts.
Requiere ETABS abierto con un modelo (nuevo o existente).
"""
import comtypes.client
import sys

_model = None

# ETABS unit enums
TONF_M_C = 9
KGF_M_C = 6
KGF_CM_C = 7


def get_model():
    """Conectar a ETABS y retornar SapModel. Reutiliza conexion."""
    global _model
    if _model is not None:
        return _model

    try:
        obj = comtypes.client.CreateObject('CSI.ETABS.API.ETABSObject')
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a ETABS: {e}")
        print("Asegurate de tener ETABS abierto.")
        sys.exit(1)

    _model = obj.SapModel
    # Fijar unidades a tonf, m, C
    _model.SetPresentUnits(TONF_M_C)
    print("[OK] Conectado a ETABS (tonf_m_C)")
    return _model


def set_units_kgf_cm(m):
    """Cambiar a kgf, cm, C (para definir materiales)."""
    m.SetPresentUnits(KGF_CM_C)


def set_units_tonf_m(m):
    """Volver a tonf, m, C."""
    m.SetPresentUnits(TONF_M_C)
