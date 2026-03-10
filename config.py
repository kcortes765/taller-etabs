"""
00_config.py — Configuracion completa del Edificio 1 (20 pisos, muros)
Fuente: Enunciado Taller ADSE 1S-2026, Prof. Music
"""

# ============================================================
# GRILLA — Ejes numerados (dir Y/horizontal) y letrados (dir X/vertical)
# ============================================================

# Ejes numerados: posicion X en metros (desde origen)
GRID_X = {
    '1':  0.000,
    '2':  3.125,
    '3':  3.825,
    '4':  9.295,
    '5':  9.895,
    '6':  15.465,
    '7':  16.015,
    '8':  18.565,
    '9':  18.990,
    '10': 21.665,
    '11': 24.990,
    '12': 26.315,
    '13': 27.834,
    '14': 32.435,
    '15': 34.005,
    '16': 37.130,
    '17': 38.505,
}

# Ejes letrados: posicion Y en metros (desde origen)
GRID_Y = {
    'A': 0.000,
    'B': 0.701,
    'C': 6.446,
    'D': 7.996,
    'E': 10.716,
    'F': 13.821,
}

# Listas ordenadas para facilitar iteracion
GRID_X_NAMES = list(GRID_X.keys())   # ['1','2',...,'17']
GRID_X_VALS  = list(GRID_X.values())
GRID_Y_NAMES = list(GRID_Y.keys())   # ['A','B','C','D','E','F']
GRID_Y_VALS  = list(GRID_Y.values())

# ============================================================
# PISOS
# ============================================================
N_STORIES = 20
STORY_HEIGHT_1 = 3.4    # Piso 1 (m)
STORY_HEIGHT_TYP = 2.6  # Pisos 2-20 (m)

# Generar lista de alturas: [3.4, 2.6, 2.6, ..., 2.6]
STORY_HEIGHTS = [STORY_HEIGHT_1] + [STORY_HEIGHT_TYP] * (N_STORIES - 1)
# Nombres de piso
STORY_NAMES = [f'Piso{i}' for i in range(1, N_STORIES + 1)]
# Elevaciones acumuladas
STORY_ELEVATIONS = []
elev = 0.0
for h in STORY_HEIGHTS:
    elev += h
    STORY_ELEVATIONS.append(round(elev, 3))

# ============================================================
# MATERIALES Y SECCIONES
# ============================================================
FC_KGF_CM2 = 300.0
FC_MPA = 30.0
EC_MPA = 4700 * (FC_MPA ** 0.5)
EC_KGF_CM2 = EC_MPA * 10
GAMMA_HA = 2.5
POISSON_CONC = 0.2

FY_KGF_CM2 = 4200.0
FY_MPA = 420.0
ES_MPA = 200000.0
ES_KGF_CM2 = ES_MPA * 10
GAMMA_ACERO = 7.85
POISSON_STEEL = 0.3

VIGA_B = 0.20
VIGA_H = 0.60
VIGA_NAME = 'VI20x60G30'

MURO_30_NAME = 'MHA30G30'
MURO_30_ESP  = 0.30
MURO_20_NAME = 'MHA20G30'
MURO_20_ESP  = 0.20

LOSA_NAME = 'Losa15G30'
LOSA_ESP  = 0.15

# ============================================================
# CARGAS Y PARAMETROS SISMICOS
# ============================================================
SCP_OFICINA, SCP_PASILLO, SCT_TECHO = 250.0, 500.0, 100.0
TERP_PISO, TERT_TECHO = 140.0, 100.0
ZONA, AO_G, SUELO, CATEGORIA, I_FACTOR, RO_MUROS, G_ACCEL = 3, 0.40, 'C', 'II', 1.0, 11, 9.81
S_SUELO, TO_SUELO, T_PRIME, N_SUELO, P_SUELO = 1.05, 0.40, 0.45, 1.40, 1.60

# ============================================================
# MUROS — Posiciones exactas segun planos page3, page6 y page7
# ============================================================

# --- MUROS DIRECCION Y (Verticales) ---
# Regla: Ejes 1,3,4,5,7,12,13,14,16,17 son de 30cm. El resto 20cm.
# Crucial: NO cruzan el pasillo (entre C y D). Se dividen en bloque sur (A-C) y norte (D-F).

MUROS_DIR_Y = [
    ('1',  GRID_X['1'],  GRID_Y['A'], GRID_Y['C'], MURO_30_ESP), # Solo sur
    ('2',  GRID_X['2'],  GRID_Y['A'], GRID_Y['B'], MURO_20_ESP), # Stub sur
    ('2',  GRID_X['2'],  GRID_Y['D'], GRID_Y['F'], MURO_20_ESP), # Stub norte
    ('3',  GRID_X['3'],  GRID_Y['A'], GRID_Y['C'], MURO_30_ESP),
    ('3',  GRID_X['3'],  GRID_Y['D'], GRID_Y['F'], MURO_30_ESP),
    ('4',  GRID_X['4'],  GRID_Y['A'], GRID_Y['C'], MURO_30_ESP),
    ('4',  GRID_X['4'],  GRID_Y['D'], GRID_Y['F'], MURO_30_ESP),
    ('5',  GRID_X['5'],  GRID_Y['A'], GRID_Y['C'], MURO_30_ESP),
    ('5',  GRID_X['5'],  GRID_Y['D'], GRID_Y['F'], MURO_30_ESP),
    ('6',  GRID_X['6'],  GRID_Y['D'], GRID_Y['F'], MURO_20_ESP), # Solo norte
    ('7',  GRID_X['7'],  GRID_Y['D'], GRID_Y['F'], MURO_30_ESP), # Solo norte
    ('8',  GRID_X['8'],  GRID_Y['A'], GRID_Y['B'], MURO_20_ESP), # Stub sur
    ('9',  GRID_X['9'],  GRID_Y['A'], GRID_Y['B'], MURO_20_ESP), # Stub sur
    ('10', GRID_X['10'], GRID_Y['A'], GRID_Y['B'], MURO_20_ESP), # Stub sur
    ('10', GRID_X['10'], GRID_Y['D'], GRID_Y['F'], MURO_20_ESP), # Pared izq shaft
    ('11', GRID_X['11'], GRID_Y['D'], GRID_Y['F'], MURO_20_ESP), # Pared der shaft
    ('12', GRID_X['12'], GRID_Y['A'], GRID_Y['C'], MURO_30_ESP),
    ('12', GRID_X['12'], GRID_Y['D'], GRID_Y['F'], MURO_30_ESP),
    ('13', GRID_X['13'], GRID_Y['A'], GRID_Y['C'], MURO_30_ESP),
    ('13', GRID_X['13'], GRID_Y['D'], GRID_Y['F'], MURO_30_ESP),
    ('14', GRID_X['14'], GRID_Y['A'], GRID_Y['C'], MURO_30_ESP),
    ('14', GRID_X['14'], GRID_Y['D'], GRID_Y['F'], MURO_30_ESP),
    ('15', GRID_X['15'], GRID_Y['D'], GRID_Y['F'], MURO_20_ESP), # Solo norte
    ('16', GRID_X['16'], GRID_Y['A'], GRID_Y['C'], MURO_30_ESP),
    ('16', GRID_X['16'], GRID_Y['D'], GRID_Y['F'], MURO_30_ESP),
    ('17', GRID_X['17'], GRID_Y['A'], GRID_Y['C'], MURO_30_ESP), # Solo sur
]

# --- MUROS DIRECCION X (Horizontales) ---
# Validado contra Elevacion Eje C y Elevacion Eje D (page6).
# Regla: Eje C entre 3-6 y 10-14 son 30cm. Resto 20cm.

MUROS_DIR_X = [
    # Eje A: Stubs visibles en plano de muros (page3)
    ('A', GRID_Y['A'], GRID_X['2'],  GRID_X['3'],  MURO_20_ESP),
    ('A', GRID_Y['A'], GRID_X['4'],  GRID_X['5'],  MURO_20_ESP),
    ('A', GRID_Y['A'], GRID_X['8'],  GRID_X['9'],  MURO_20_ESP),
    ('A', GRID_Y['A'], GRID_X['12'], GRID_X['13'], MURO_20_ESP),
    ('A', GRID_Y['A'], GRID_X['16'], GRID_X['17'], MURO_20_ESP),

    # Eje C: Basado en Elevacion Eje C (page6) que muestra 8 machones
    ('C', GRID_Y['C'], GRID_X['1'],  GRID_X['3'],  MURO_20_ESP),
    ('C', GRID_Y['C'], GRID_X['3'],  GRID_X['4'],  MURO_30_ESP),
    ('C', GRID_Y['C'], GRID_X['5'],  GRID_X['6'],  MURO_30_ESP),
    ('C', GRID_Y['C'], GRID_X['7'],  GRID_X['8'],  MURO_20_ESP),
    ('C', GRID_Y['C'], GRID_X['10'], GRID_X['11'], MURO_30_ESP),
    ('C', GRID_Y['C'], GRID_X['11'], GRID_X['12'], MURO_30_ESP),
    ('C', GRID_Y['C'], GRID_X['13'], GRID_X['14'], MURO_30_ESP),
    ('C', GRID_Y['C'], GRID_X['14'], GRID_X['17'], MURO_20_ESP),

    # Eje D: Basado en Elevacion Eje D (page6) que muestra 5 machones
    ('D', GRID_Y['D'], GRID_X['2'],  GRID_X['3'],  MURO_20_ESP),
    ('D', GRID_Y['D'], GRID_X['4'],  GRID_X['5'],  MURO_20_ESP),
    ('D', GRID_Y['D'], GRID_X['10'], GRID_X['11'], MURO_20_ESP),
    ('D', GRID_Y['D'], GRID_X['12'], GRID_X['13'], MURO_20_ESP),
    ('D', GRID_Y['D'], GRID_X['14'], GRID_X['15'], MURO_20_ESP),

    # Eje E: Stubs superiores del pasillo (visibles en page3)
    ('E', GRID_Y['E'], GRID_X['2'],  GRID_X['3'],  MURO_20_ESP),
    ('E', GRID_Y['E'], GRID_X['4'],  GRID_X['5'],  MURO_20_ESP),
    ('E', GRID_Y['E'], GRID_X['10'], GRID_X['11'], MURO_20_ESP),
    ('E', GRID_Y['E'], GRID_X['14'], GRID_X['15'], MURO_20_ESP),

    # Eje F: muro horizontal superior centrado en eje 10.
    # Longitud total = 7.70 m, medida desde la figura "Longitud de Muros" (pag. 3).
    # No coincide exactamente con separaciones de ejes, por eso se usa coordenada directa.
    ('F', GRID_Y['F'], GRID_X['10'] - 4.25, GRID_X['10'] + 3.45, MURO_20_ESP),
]

# ============================================================
# VIGAS — Posiciones (del plano pag 2: lineas azules)
# ============================================================
VIGAS_EJE_A = [
    (GRID_Y['A'], GRID_X['1'],  GRID_X['2']),
    (GRID_Y['A'], GRID_X['3'],  GRID_X['4']),
    (GRID_Y['A'], GRID_X['5'],  GRID_X['6']),
    (GRID_Y['A'], GRID_X['7'],  GRID_X['8']),
    (GRID_Y['A'], GRID_X['9'],  GRID_X['10']),
    (GRID_Y['A'], GRID_X['10'], GRID_X['11']),
    (GRID_Y['A'], GRID_X['11'], GRID_X['12']),
    (GRID_Y['A'], GRID_X['13'], GRID_X['14']),
    (GRID_Y['A'], GRID_X['14'], GRID_X['15']),
    (GRID_Y['A'], GRID_X['15'], GRID_X['16']),
]

VIGAS_EJE_F = [
    (GRID_Y['F'], GRID_X['2'],  GRID_X['3']),
    (GRID_Y['F'], GRID_X['3'],  GRID_X['4']),
    (GRID_Y['F'], GRID_X['5'],  GRID_X['6']),
    (GRID_Y['F'], GRID_X['6'],  GRID_X['7']),
    (GRID_Y['F'], GRID_X['11'], GRID_X['12']),
    (GRID_Y['F'], GRID_X['12'], GRID_X['13']),
    (GRID_Y['F'], GRID_X['13'], GRID_X['14']),
    (GRID_Y['F'], GRID_X['15'], GRID_X['16']),
]

VIGAS_INTERIORES = [
    (GRID_Y['B'], GRID_X['1'],  GRID_X['2']),
    (GRID_Y['B'], GRID_X['3'],  GRID_X['4']),
    (GRID_Y['B'], GRID_X['5'],  GRID_X['6']),
    (GRID_Y['B'], GRID_X['6'],  GRID_X['7']),
    (GRID_Y['B'], GRID_X['7'],  GRID_X['8']),
    (GRID_Y['B'], GRID_X['9'],  GRID_X['10']),
    (GRID_Y['B'], GRID_X['10'], GRID_X['11']),
    (GRID_Y['B'], GRID_X['11'], GRID_X['12']),
    (GRID_Y['B'], GRID_X['13'], GRID_X['14']),
    (GRID_Y['B'], GRID_X['14'], GRID_X['15']),
    (GRID_Y['B'], GRID_X['15'], GRID_X['16']),
    (GRID_Y['B'], GRID_X['16'], GRID_X['17']),
]

VIGAS = VIGAS_EJE_A + VIGAS_EJE_F + VIGAS_INTERIORES

# ============================================================
# LOSAS - Huella levantada desde Enunciado Taller (paginas 2 y 4)
# ============================================================
def _rect_axes(x_ini, x_fin, y_ini, y_fin):
    return (GRID_X[x_ini], GRID_Y[y_ini], GRID_X[x_fin], GRID_Y[y_fin])

# Paneles diseñados para dejar vacio el Shaft (entre ejes 9-11 y C-D)
# y la zona de acceso sur (entre ejes 1-3 y A-B)
SLAB_PANELS_FLOOR = [
    _rect_axes('3', '6', 'A', 'B'),
    _rect_axes('7', '8', 'A', 'B'),
    _rect_axes('9', '16', 'A', 'B'),
    _rect_axes('3', '17', 'B', 'C'),
    _rect_axes('3', '9', 'C', 'D'),
    _rect_axes('11', '17', 'C', 'D'),
    _rect_axes('3', '17', 'D', 'F'),
]

SLAB_PANELS_ROOF = [
    _rect_axes('3', '16', 'A', 'B'),
    _rect_axes('3', '17', 'B', 'C'),
    _rect_axes('3', '9', 'C', 'D'),
    _rect_axes('11', '17', 'C', 'D'),
    _rect_axes('3', '17', 'D', 'F'),
]

def _rect_area(panel):
    x0, y0, x1, y1 = panel
    return abs((x1 - x0) * (y1 - y0))

def _rect_centroid(panel):
    x0, y0, x1, y1 = panel
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0)

def _panels_area(panels):
    return sum(_rect_area(panel) for panel in panels)

def _panels_centroid(panels):
    total_area = _panels_area(panels)
    if total_area <= 0:
        return (0.0, 0.0)
    sum_x, sum_y = 0.0, 0.0
    for panel in panels:
        area = _rect_area(panel)
        cx, cy = _rect_centroid(panel)
        sum_x += area * cx
        sum_y += area * cy
    return (sum_x / total_area, sum_y / total_area)

# ============================================================
# LOAD PATTERNS & TORSION
# ============================================================
LOAD_PATTERNS = {
    'PP':   'Dead',
    'SCP':  'Live',
    'SCT':  'Roof Live',
    'TERP': 'Super Dead',
    'TERT': 'Super Dead',
}

LX_PLANTA = max(GRID_X.values()) - min(GRID_X.values())
LY_PLANTA = max(GRID_Y.values()) - min(GRID_Y.values())
EA_X = 0.05 * LX_PLANTA
EA_Y = 0.05 * LY_PLANTA

AREA_PISO_TIPO = _panels_area(SLAB_PANELS_FLOOR)
AREA_TECHO = _panels_area(SLAB_PANELS_ROOF)
AREA_TOTAL_NIVELES = AREA_PISO_TIPO * (N_STORIES - 1) + AREA_TECHO
AREA_PLANTA = AREA_TOTAL_NIVELES / N_STORIES
AREA_ENVOLVENTE = LX_PLANTA * LY_PLANTA
CM_X, CM_Y = _panels_centroid(SLAB_PANELS_FLOOR)
CM_X_TECHO, CM_Y_TECHO = _panels_centroid(SLAB_PANELS_ROOF)

# ============================================================
# R* (DS61)
# ============================================================
def calc_R_star(Ro, T_star):
    """Calcula R* segun DS61 Art. 5.1.2."""
    if Ro <= 1:
        return 1.0
    T0r = 0.1 * Ro**2 / (Ro - 1)
    if T_star >= T0r:
        return 1.0 + (Ro - 1.0) * T_star / (0.1 * Ro**2 + T_star)
    else:
        return 1.0 + (Ro - 1.0) * (T_star / T0r) ** 0.5

if __name__ == '__main__':
    print(f"Edificio 1 - {N_STORIES} pisos")
    print(f"H total: {STORY_ELEVATIONS[-1]} m")
    print(f"Grilla: {len(GRID_X)} ejes X, {len(GRID_Y)} ejes Y")
    print(f"Muros dir Y: {len(MUROS_DIR_Y)}")
    print(f"Muros dir X: {len(MUROS_DIR_X)}")
    print(f"Vigas: {len(VIGAS)}")
    print(f"Area piso tipo: {AREA_PISO_TIPO:.1f} m2")
    print(f"CM piso tipo: ({CM_X:.3f}, {CM_Y:.3f}) m")
    print(f"R*(Ro=11, T*=1.5s) = {calc_R_star(11, 1.5):.2f}")
