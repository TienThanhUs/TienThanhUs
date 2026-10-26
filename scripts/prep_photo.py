#!/usr/bin/env python3
"""Prep a photo for ASCII conversion.

Pipeline: remove background (rembg) -> crop to subject -> grayscale ->
CLAHE local contrast -> composite on pure white.

Usage: python scripts/prep_photo.py <photo.jpg> [--head-frac 1.0]
Writes source-prepped.png next to the scripts dir's parent.
"""
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

HEAD_FRAC = 1.05  # crop height = bbox_width * HEAD_FRAC, taken from the top


def main() -> None:
    src = sys.argv[1]
    head_frac = HEAD_FRAC
    if "--head-frac" in sys.argv:
        head_frac = float(sys.argv[sys.argv.index("--head-frac") + 1])

    img = Image.open(src).convert("RGBA")
    cut = remove(img)  # RGBA with transparent background

    alpha = np.array(cut)[:, :, 3]
    ys, xs = np.where(alpha > 20)
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    # Head-and-shoulders crop: from the top of the subject, height
    # proportional to subject width so the face dominates the grid.
    w = x1 - x0
    crop_h = min(int(w * head_frac), y1 - y0)
    pad = int(w * 0.04)
    box = (
        max(0, x0 - pad),
        max(0, y0 - pad),
        min(cut.width, x1 + pad),
        min(cut.height, y0 + crop_h + pad),
    )
    cut = cut.crop(box)

    # Composite onto pure white so background maps to the blank end of the ramp
    white = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(white, cut).convert("L")

    # CLAHE: local contrast so a flatly lit face gets real highlights/shadows
    gray = np.array(flat)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    boosted = clahe.apply(gray)
    # Re-whiten the background: CLAHE darkens flat white regions slightly
    boosted[np.array(Image.alpha_composite(
        Image.new("RGBA", cut.size, (0, 0, 0, 255)), cut).convert("L")) < 8] = 255

    Image.fromarray(boosted).save("source-prepped.png")
    print(f"wrote source-prepped.png {boosted.shape[1]}x{boosted.shape[0]}")


if __name__ == "__main__":
    main()
