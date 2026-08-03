"""
wplace.live — Bot timelapse multi-tuiles.

Ce script :
1. Télécharge 6 tuiles PNG depuis le backend de wplace.live
2. Les assemble en une grille 2×3 (2000×3000 px)
3. Compare avec la référence précédente
4. Si au moins 1 pixel a changé → sauvegarde la frame pour le timelapse
5. Met à jour la référence pour le prochain run
"""

import os
import sys
import io
from datetime import datetime, timezone
import requests
from PIL import Image
import numpy as np


# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────

# Grille de tuiles : (colonne, ligne) dans l'image finale
# L'image est assemblée comme suit :
#   col 0 (x=1053)  |  col 1 (x=1054)
#   row 0 (y=735)   |  row 0 (y=735)
#   row 1 (y=736)   |  row 1 (y=736)
#   row 2 (y=737)   |  row 2 (y=737)
TILES = [
    # (col, row, tile_x, tile_y)
    (0, 0, 1053, 735),  # tile 4 → haut-gauche
    (1, 0, 1054, 735),  # tile 1 → haut-droite
    (0, 1, 1053, 736),  # tile 5 → milieu-gauche
    (1, 1, 1054, 736),  # tile 2 → milieu-droite
    (0, 2, 1053, 737),  # tile 6 → bas-gauche
    (1, 2, 1054, 737),  # tile 3 → bas-droite
]

TILE_SIZE = 1000  # chaque tuile fait 1000×1000 px
GRID_COLS = 2
GRID_ROWS = 3

# Tolérance de couleur pour ignorer le bruit de compression (0-255)
COLOR_TOLERANCE = int(os.environ.get("TL_COLOR_TOLERANCE") or "5")

# Dossier de sortie pour les frames du timelapse
FRAMES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "frames"
)

# Chemin de l'image de référence
REFERENCE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "reference.png"
)

BASE_URL = "https://backend.wplace.live/files/s0/tiles"


def download_tile(tile_x: int, tile_y: int) -> Image.Image:
    """Télécharge une tuile depuis le backend wplace.live."""
    url = f"{BASE_URL}/{tile_x}/{tile_y}.png"
    print(f"  📥 Tuile ({tile_x}, {tile_y}) : {url}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return Image.open(io.BytesIO(resp.content)).convert("RGB")


def download_and_stitch() -> Image.Image:
    """Télécharge les 6 tuiles et les assemble en une grille 2×3."""
    print("📥 Téléchargement des 6 tuiles...")
    canvas = Image.new(
        "RGB",
        (GRID_COLS * TILE_SIZE, GRID_ROWS * TILE_SIZE),
    )

    for col, row, tx, ty in TILES:
        tile_img = download_tile(tx, ty)
        x_offset = col * TILE_SIZE
        y_offset = row * TILE_SIZE
        canvas.paste(tile_img, (x_offset, y_offset))

    print(f"🖼️  Image assemblée : {canvas.size[0]}×{canvas.size[1]} px")
    return canvas


def has_changed(current: Image.Image, reference: Image.Image) -> tuple[bool, int]:
    """Compare deux images. Retourne (a_changé, nombre_de_pixels_modifiés).

    Un pixel est considéré "modifié" si la différence absolue sur au
    moins un canal RGB dépasse COLOR_TOLERANCE.
    """
    if current.size != reference.size:
        print("⚠️  Taille différente → considéré comme changement total")
        return True, current.size[0] * current.size[1]

    arr_cur = np.array(current, dtype=np.int16)
    arr_ref = np.array(reference, dtype=np.int16)

    diff = np.abs(arr_cur - arr_ref)
    max_diff_per_pixel = diff.max(axis=2)

    changed_mask = max_diff_per_pixel > COLOR_TOLERANCE
    num_changed = int(changed_mask.sum())

    print(f"🔍 Pixels modifiés : {num_changed} (tolérance : {COLOR_TOLERANCE})")
    return num_changed > 0, num_changed


def save_frame(image: Image.Image) -> str:
    """Sauvegarde une frame horodatée dans le dossier frames/."""
    os.makedirs(FRAMES_DIR, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"frame_{timestamp}.png"
    filepath = os.path.join(FRAMES_DIR, filename)

    image.save(filepath, format="PNG")
    print(f"🎞️  Frame sauvegardée : {filepath}")
    return filepath


def main() -> None:
    # 1. Télécharger et assembler les tuiles
    current_image = download_and_stitch()

    # 2. Charger la référence (si elle existe)
    if os.path.isfile(REFERENCE_PATH):
        reference_image = Image.open(REFERENCE_PATH).convert("RGB")
        print(f"📂 Référence chargée : {REFERENCE_PATH}")
    else:
        # Premier run : sauvegarder comme référence + première frame
        current_image.save(REFERENCE_PATH)
        save_frame(current_image)
        print(
            "🆕 Aucune référence trouvée — image initiale sauvegardée "
            "comme référence et première frame du timelapse."
        )
        return

    # 3. Comparer
    changed, num_pixels = has_changed(current_image, reference_image)

    # 4. Si changement → sauvegarder une frame
    if changed:
        save_frame(current_image)
        print(f"✅ Changement détecté ({num_pixels} pixels) → frame enregistrée !")
    else:
        print("😴 Aucun changement détecté → pas de nouvelle frame.")

    # 5. Mettre à jour la référence
    current_image.save(REFERENCE_PATH)
    print(f"💾 Référence mise à jour : {REFERENCE_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"❌ Erreur fatale : {exc}", file=sys.stderr)
        sys.exit(1)
