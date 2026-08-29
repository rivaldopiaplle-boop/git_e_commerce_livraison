# -*- coding: utf-8 -*-
"""Analyse le logo fourni et fabrique les declinaisons utilisables sur le web."""
import os
from PIL import Image

RACINE = r"c:\Users\HP\Desktop\vscode\trainning\Devops\e-commerce-livraison"
SOURCE = os.path.join(RACINE, "plan-organisation", "logo.png")

img = Image.open(SOURCE).convert("RGB")
print("source : %dx%d" % img.size)

# ── Palette reelle du logo ────────────────────────────────────────────────
reduite = img.resize((160, 160)).quantize(colors=10, method=Image.Quantize.FASTOCTREE)
palette = reduite.getpalette()
compte = sorted(reduite.getcolors(), reverse=True)
total = sum(n for n, _ in compte)
print("\ncouleurs dominantes :")
for n, index in compte:
    r, v, b = palette[index * 3: index * 3 + 3]
    print("  #%02x%02x%02x  %5.1f %%" % (r, v, b, 100.0 * n / total))

# ── Declinaisons web ──────────────────────────────────────────────────────
PUBLIC = os.path.join(RACINE, "frontend-web", "public")
if not os.path.isdir(PUBLIC):
    os.makedirs(PUBLIC)

sorties = []
for taille in (512, 256, 192):
    petit = img.resize((taille, taille), Image.LANCZOS)
    chemin_webp = os.path.join(PUBLIC, "logo-rivdinde-%d.webp" % taille)
    petit.save(chemin_webp, "WEBP", quality=86, method=6)
    sorties.append(chemin_webp)
    if taille in (512, 192):
        chemin_png = os.path.join(PUBLIC, "logo-rivdinde-%d.png" % taille)
        petit.save(chemin_png, "PNG", optimize=True)
        sorties.append(chemin_png)

print("\ndeclinaisons ecrites :")
for c in sorties:
    print("  %-46s %6.1f Ko" % (os.path.basename(c), os.path.getsize(c) / 1024))

print("\ngain : %.1f Mo -> %.1f Ko pour la version affichee (512 WebP)" % (
    os.path.getsize(SOURCE) / 1048576,
    os.path.getsize(os.path.join(PUBLIC, "logo-rivdinde-512.webp")) / 1024,
))
