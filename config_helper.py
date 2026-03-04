"""
config_helper.py — Conexion a ETABS 19.
IMPORTANTE: Antes de correr, asegurar que SOLO ETABS 19 este abierto.
"""
import comtypes.client
import sys
import time

_model = None

TONF_M_C = 9
KGF_M_C = 6
KGF_CM_C = 7


def get_model(retries=5, wait=3):
    """Conectar al ETABS que esta corriendo. Reintenta si no esta listo."""
    global _model
    if _model is not None:
        return _model

    for attempt in range(1, retries + 1):
        # Metodo 1: GetActiveObject (conecta al ETABS ya abierto)
        try:
            obj = comtypes.client.GetActiveObject('CSI.ETABS.API.ETABSObject')
            _model = obj.SapModel
            _model.GetPresentUnits()  # test rapido
            _model.SetPresentUnits(TONF_M_C)
            print("[OK] Conectado a ETABS via GetActiveObject (tonf_m_C)")
            return _model
        except Exception as e1:
            pass

        # Metodo 2: Helper + GetObject (conecta al proceso existente)
        try:
            helper = comtypes.client.CreateObject('ETABSv1.Helper')
            helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
            obj = helper.GetObject('CSI.ETABS.API.ETABSObject')
            _model = obj.SapModel
            _model.GetPresentUnits()
            _model.SetPresentUnits(TONF_M_C)
            print("[OK] Conectado a ETABS via Helper.GetObject (tonf_m_C)")
            return _model
        except Exception as e2:
            pass

        # Metodo 3: CreateObject (lanza nueva instancia — ultimo recurso)
        try:
            obj = comtypes.client.CreateObject('CSI.ETABS.API.ETABSObject')
            _model = obj.SapModel
            _model.GetPresentUnits()
            _model.SetPresentUnits(TONF_M_C)
            print("[OK] Conectado a ETABS via CreateObject (tonf_m_C)")
            return _model
        except Exception as e3:
            pass

        if attempt < retries:
            print(f"  Intento {attempt}/{retries} fallido, esperando {wait}s (ETABS cargando?)...")
            time.sleep(wait)

    print("[ERROR] No se pudo conectar a ETABS despues de varios intentos.")
    print("Verifica que:")
    print("  1. ETABS 19 este completamente abierto (espera a que cargue)")
    print("  2. No haya otra version de ETABS corriendo")
    print("  3. Python sea de 64-bit (igual que ETABS)")
    sys.exit(1)


def set_units_kgf_cm(m):
    m.SetPresentUnits(KGF_CM_C)

def set_units_tonf_m(m):
    m.SetPresentUnits(TONF_M_C)
