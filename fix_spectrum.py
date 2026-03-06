"""fix_spectrum.py — Regenera espectro_nch433.txt con formato compatible ETABS."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import S_SUELO, AO_G, TO_SUELO, P_SUELO

lines = []
T = 0.0
while T <= 5.01:
    if T == 0.0:
        sa = S_SUELO * AO_G
    else:
        ratio = TO_SUELO / T
        alpha = (1.0 + 4.5 * ratio**P_SUELO) / (1.0 + ratio**3)
        sa = S_SUELO * AO_G * alpha
    lines.append("%.4f %.6f" % (T, sa))
    T = round(T + 0.05, 4)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "espectro_nch433.txt")
with open(out, "w") as f:
    f.write("\n".join(lines))

print("OK — %d puntos escritos en: %s" % (len(lines), out))
print("Primeras 3 lineas:")
for line in lines[:3]:
    print("  " + line)
