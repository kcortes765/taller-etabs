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
# H total = 3.4 + 19*2.6 = 52.8 m

# ============================================================
# MATERIALES
# ============================================================
# Hormigon G30: f'c = 300 kgf/cm2 = 30 MPa
FC_KGF_CM2 = 300.0
FC_MPA = 30.0
EC_MPA = 4700 * (FC_MPA ** 0.5)   # ~25742 MPa
EC_KGF_CM2 = EC_MPA * 10          # ~257420 kgf/cm2
GAMMA_HA = 2.5  # tonf/m3
POISSON_CONC = 0.2

# Acero A630-420H
FY_KGF_CM2 = 4200.0
FY_MPA = 420.0
ES_MPA = 200000.0  # modulo elasticidad acero
ES_KGF_CM2 = ES_MPA * 10
GAMMA_ACERO = 7.85  # tonf/m3
POISSON_STEEL = 0.3

# ============================================================
# SECCIONES
# ============================================================
# Vigas invertidas (todas iguales)
VIGA_B = 0.20   # m (ancho)
VIGA_H = 0.60   # m (alto)
VIGA_NAME = 'VI20x60G30'

# Muros
MURO_30_NAME = 'MHA30G30'
MURO_30_ESP  = 0.30  # m
MURO_20_NAME = 'MHA20G30'
MURO_20_ESP  = 0.20  # m

# Losa
LOSA_NAME = 'Losa15G30'
LOSA_ESP  = 0.15  # m

# ============================================================
# CARGAS (kgf/m2)
# ============================================================
SCP_OFICINA  = 250.0   # sobrecarga piso tipo (oficinas)
SCP_PASILLO  = 500.0   # sobrecarga pasillos
SCT_TECHO    = 100.0   # sobrecarga techo
TERP_PISO    = 140.0   # terminaciones piso tipo
TERT_TECHO   = 100.0   # terminaciones techo

# ============================================================
# PARAMETROS SISMICOS
# ============================================================
ZONA = 3
AO_G = 0.40        # Ao/g para Zona 3
SUELO = 'C'
CATEGORIA = 'II'   # Oficinas
I_FACTOR = 1.0     # Factor de importancia
RO_MUROS = 11      # Factor de reduccion base (muros HA)
G_ACCEL = 9.81     # m/s2

# Parametros suelo tipo C (DS61 Tabla 6.3)
S_SUELO = 1.05
TO_SUELO = 0.40    # T0 (s)
T_PRIME = 0.45     # T' (s)
N_SUELO = 1.40
P_SUELO = 1.60

# ============================================================
# MUROS — Posiciones exactas extraidas de planos (paginas 2-4)
# Formato: (eje_fijo, coord_fijo, coord_inicio, coord_fin, espesor_m)
#   - Para muros dir Y (verticales en planta): eje_fijo = eje X numerico
#     coord_fijo = X, coord_inicio/fin = Y_inicio/Y_fin
#   - Para muros dir X (horizontales en planta): eje_fijo = eje Y letrado
#     coord_fijo = Y, coord_inicio/fin = X_inicio/X_fin
# ============================================================

# --- MUROS DIRECCION Y (en ejes numerados, van de A/B a F) ---
# Regla: ejes 1,3,4,5,7,12,13,14,16,17 = 30cm, otros = 20cm
# Longitudes medidas del plano pag 3

# Eje 1: muro en A-B (corto, ~0.701m) NO, del plano se ve que eje 1 tiene
#   un muro largo de A a C (abajo) — revisando planta pag 2:
#   Eje 1: muro de A a B (0.701m) en la base inferior

# Del plano de planta (pag 2) y longitudes (pag 3), interpreto:
# Los muros en dir Y estan en los ejes numerados, corriendo entre ejes letrados

MUROS_DIR_Y = [
    # eje, x_coord, y_start, y_end, espesor
    # --- Eje 1 (x=0, e=30cm) ---
    ('1', GRID_X['1'], GRID_Y['A'], GRID_Y['C'], MURO_30_ESP),

    # --- Eje 2 (x=3.125, e=20cm) ---
    ('2', GRID_X['2'], GRID_Y['A'], GRID_Y['B'], MURO_20_ESP),
    ('2', GRID_X['2'], GRID_Y['C'], GRID_Y['F'], MURO_20_ESP),

    # --- Eje 3 (x=3.825, e=30cm) ---
    ('3', GRID_X['3'], GRID_Y['A'], GRID_Y['B'], MURO_30_ESP),
    ('3', GRID_X['3'], GRID_Y['C'], GRID_Y['F'], MURO_30_ESP),

    # --- Eje 4 (x=9.295, e=30cm) --- muro Tee (el ala es en C)
    ('4', GRID_X['4'], GRID_Y['A'], GRID_Y['B'], MURO_30_ESP),
    ('4', GRID_X['4'], GRID_Y['C'], GRID_Y['F'], MURO_30_ESP),

    # --- Eje 5 (x=9.895, e=30cm) ---
    ('5', GRID_X['5'], GRID_Y['A'], GRID_Y['B'], MURO_30_ESP),
    ('5', GRID_X['5'], GRID_Y['C'], GRID_Y['F'], MURO_30_ESP),

    # --- Eje 6 (x=15.465, e=20cm) ---
    ('6', GRID_X['6'], GRID_Y['C'], GRID_Y['F'], MURO_20_ESP),

    # --- Eje 7 (x=16.015, e=30cm) ---
    ('7', GRID_X['7'], GRID_Y['C'], GRID_Y['F'], MURO_30_ESP),

    # --- Eje 8 (x=18.565, e=20cm) ---
    ('8', GRID_X['8'], GRID_Y['A'], GRID_Y['B'], MURO_20_ESP),

    # --- Eje 9 (x=18.990, e=20cm) ---
    ('9', GRID_X['9'], GRID_Y['A'], GRID_Y['B'], MURO_20_ESP),

    # --- Eje 10 (x=21.665, e=20cm) ---
    # Del plano: eje 10 tiene muro largo en parte superior (C-F) con abertura
    ('10', GRID_X['10'], GRID_Y['A'], GRID_Y['B'], MURO_20_ESP),

    # --- Eje 11 (x=24.990, e=20cm) ---
    ('11', GRID_X['11'], GRID_Y['C'], GRID_Y['F'], MURO_20_ESP),

    # --- Eje 12 (x=26.315, e=30cm) ---
    ('12', GRID_X['12'], GRID_Y['A'], GRID_Y['B'], MURO_30_ESP),
    ('12', GRID_X['12'], GRID_Y['C'], GRID_Y['F'], MURO_30_ESP),

    # --- Eje 13 (x=27.834, e=30cm) ---
    ('13', GRID_X['13'], GRID_Y['A'], GRID_Y['B'], MURO_30_ESP),
    ('13', GRID_X['13'], GRID_Y['C'], GRID_Y['F'], MURO_30_ESP),

    # --- Eje 14 (x=32.435, e=30cm) ---
    ('14', GRID_X['14'], GRID_Y['A'], GRID_Y['B'], MURO_30_ESP),
    ('14', GRID_X['14'], GRID_Y['C'], GRID_Y['F'], MURO_30_ESP),

    # --- Eje 15 (x=34.005, e=20cm) ---
    ('15', GRID_X['15'], GRID_Y['C'], GRID_Y['F'], MURO_20_ESP),

    # --- Eje 16 (x=37.130, e=30cm) ---
    ('16', GRID_X['16'], GRID_Y['A'], GRID_Y['B'], MURO_30_ESP),
    ('16', GRID_X['16'], GRID_Y['C'], GRID_Y['F'], MURO_30_ESP),

    # --- Eje 17 (x=38.505, e=30cm) ---
    ('17', GRID_X['17'], GRID_Y['A'], GRID_Y['C'], MURO_30_ESP),
]

# --- MUROS DIRECCION X (en ejes letrados, van entre ejes numerados) ---
# Regla: eje C entre 3-6 y 10-14 = 30cm. Todos los demas = 20cm

MUROS_DIR_X = [
    # eje, y_coord, x_start, x_end, espesor
    # --- Eje A (y=0, e=20cm) ---
    ('A', GRID_Y['A'], GRID_X['2'],  GRID_X['3'],  MURO_20_ESP),
    ('A', GRID_Y['A'], GRID_X['4'],  GRID_X['5'],  MURO_20_ESP),
    ('A', GRID_Y['A'], GRID_X['8'],  GRID_X['9'],  MURO_20_ESP),
    ('A', GRID_Y['A'], GRID_X['12'], GRID_X['13'], MURO_20_ESP),
    ('A', GRID_Y['A'], GRID_X['16'], GRID_X['17'], MURO_20_ESP),

    # --- Eje B (y=0.701, e=20cm) ---
    # Eje B tiene vigas, no muros significativos en planta
    # (del plano se ve solo vigas azules en B)

    # --- Eje C (y=6.446) --- MUROS IMPORTANTES
    # Entre 3-6: e=30cm
    ('C', GRID_Y['C'], GRID_X['3'],  GRID_X['4'],  MURO_30_ESP),
    ('C', GRID_Y['C'], GRID_X['5'],  GRID_X['6'],  MURO_30_ESP),
    # Entre 10-14: e=30cm  (con abertura ascensor en 8-10 aprox)
    ('C', GRID_Y['C'], GRID_X['10'], GRID_X['11'], MURO_30_ESP),
    ('C', GRID_Y['C'], GRID_X['11'], GRID_X['12'], MURO_30_ESP),
    ('C', GRID_Y['C'], GRID_X['13'], GRID_X['14'], MURO_30_ESP),
    # Resto en eje C: e=20cm
    ('C', GRID_Y['C'], GRID_X['1'],  GRID_X['2'],  MURO_20_ESP),
    ('C', GRID_Y['C'], GRID_X['7'],  GRID_X['8'],  MURO_20_ESP),
    ('C', GRID_Y['C'], GRID_X['14'], GRID_X['15'], MURO_20_ESP),
    ('C', GRID_Y['C'], GRID_X['15'], GRID_X['16'], MURO_20_ESP),
    ('C', GRID_Y['C'], GRID_X['16'], GRID_X['17'], MURO_20_ESP),

    # --- Eje D (y=7.996, e=20cm) ---
    # Del plano: muros cortos en D
    ('D', GRID_Y['D'], GRID_X['2'],  GRID_X['3'],  MURO_20_ESP),
    ('D', GRID_Y['D'], GRID_X['4'],  GRID_X['5'],  MURO_20_ESP),
    ('D', GRID_Y['D'], GRID_X['12'], GRID_X['13'], MURO_20_ESP),

    # --- Eje E (y=10.716, e=20cm) ---
    ('E', GRID_Y['E'], GRID_X['2'],  GRID_X['3'],  MURO_20_ESP),
    ('E', GRID_Y['E'], GRID_X['4'],  GRID_X['5'],  MURO_20_ESP),
    ('E', GRID_Y['E'], GRID_X['10'], GRID_X['11'], MURO_20_ESP),
    ('E', GRID_Y['E'], GRID_X['14'], GRID_X['15'], MURO_20_ESP),

    # --- Eje F (y=13.821, e=20cm) ---
    # Del plano pag 7 (elevacion eje F): muros en ejes 4-5 y 14-15 solamente
    # Los otros tramos en F tienen vigas, no muros
    ('F', GRID_Y['F'], GRID_X['2'],  GRID_X['3'],  MURO_20_ESP),
    ('F', GRID_Y['F'], GRID_X['4'],  GRID_X['5'],  MURO_20_ESP),
    ('F', GRID_Y['F'], GRID_X['14'], GRID_X['15'], MURO_20_ESP),
    ('F', GRID_Y['F'], GRID_X['16'], GRID_X['17'], MURO_20_ESP),
]

# ============================================================
# VIGAS — Posiciones (del plano pag 2: lineas azules)
# Formato: (y_coord, x_start, x_end) — vigas van en dir X (horizontal)
# Todas son VI20/60G30
# ============================================================

# Vigas en eje A (y=0): conectan pares de muros
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

# Vigas en eje F (y=13.821): borde superior
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

# Vigas adicionales en ejes intermedios (B, C, D, E)
# Se agregan donde hay vigas azules visibles en planta
VIGAS_INTERIORES = [
    # Eje B (y=0.701) — vigas de acoplamiento
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

# Todas las vigas juntas
VIGAS = VIGAS_EJE_A + VIGAS_EJE_F + VIGAS_INTERIORES


# ============================================================
# NOTACION LOAD PATTERNS
# ============================================================
LOAD_PATTERNS = {
    'PP':   'Dead',       # Peso propio (auto)
    'SCP':  'Live',       # Sobrecarga piso
    'SCT':  'Roof Live',  # Sobrecarga techo
    'TERP': 'Super Dead', # Terminaciones piso
    'TERT': 'Super Dead', # Terminaciones techo
    'SEx':  'Quake',      # Sismo X
    'SEy':  'Quake',      # Sismo Y
}


# ============================================================
# DIMENSIONES DE PLANTA (para torsion accidental)
# ============================================================
LX_PLANTA = max(GRID_X.values()) - min(GRID_X.values())  # 38.505 m
LY_PLANTA = max(GRID_Y.values()) - min(GRID_Y.values())  # 13.821 m
EA_X = 0.05 * LX_PLANTA  # excentricidad accidental para sismo Y (1.925 m)
EA_Y = 0.05 * LY_PLANTA  # excentricidad accidental para sismo X (0.691 m)

# Centro geometrico aproximado de la planta
CM_X = (min(GRID_X.values()) + max(GRID_X.values())) / 2  # ~19.25 m
CM_Y = (min(GRID_Y.values()) + max(GRID_Y.values())) / 2  # ~6.91 m

# Area de planta
AREA_PLANTA = LX_PLANTA * LY_PLANTA  # ~532 m2


# ============================================================
# R* (DS61)
# ============================================================
def calc_R_star(Ro, T_star):
    """Calcula R* segun DS61 Art. 5.1.2."""
    if Ro <= 1:
        return 1.0
    T0r = 0.1 * Ro**2 / (Ro - 1)  # ~1.21 para Ro=11
    if T_star >= T0r:
        return 1.0 + (Ro - 1.0) * T_star / (0.1 * Ro**2 + T_star)
    else:
        return 1.0 + (Ro - 1.0) * (T_star / T0r) ** 0.5


if __name__ == '__main__':
    print(f"Edificio 1 — {N_STORIES} pisos")
    print(f"H total: {STORY_ELEVATIONS[-1]} m")
    print(f"Grilla: {len(GRID_X)} ejes X, {len(GRID_Y)} ejes Y")
    print(f"Planta: {LX_PLANTA:.3f} x {LY_PLANTA:.3f} m ({AREA_PLANTA:.0f} m2)")
    print(f"Muros dir Y: {len(MUROS_DIR_Y)}")
    print(f"Muros dir X: {len(MUROS_DIR_X)}")
    print(f"Vigas: {len(VIGAS)}")
    print(f"Ec = {EC_MPA:.0f} MPa")
    print(f"R*(Ro=11, T*=1.5s) = {calc_R_star(11, 1.5):.2f}")
    print(f"R*(Ro=11, T*=0.5s) = {calc_R_star(11, 0.5):.2f}")
