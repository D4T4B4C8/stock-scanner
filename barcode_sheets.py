"""
Barcode sheet generator
-----------------------
Asks for a starting ID and an ending ID, then creates Code128 barcodes
(613 x 452 px each) laid out 4 per row on A4-sized images (2480 x 3508 px, 300 DPI).

Install requirements:
    pip install python-barcode pillow
"""

import os
import sys

import barcode
from PIL import Image, ImageDraw, ImageFont

# ---------------- SETTINGS ----------------
A4_W, A4_H = 2480, 3508          # A4 at 300 DPI
BC_W, BC_H = 613, 452            # size of each barcode label
COLS = 4                         # barcodes per row
OUTPUT_DIR = "barcode_sheets"
DRAW_BORDER = True               # thin cut-line around each label
FONT_SIZE = 56
# ------------------------------------------

ROWS = A4_H // BC_H              # rows that fit on one sheet (7)
PER_SHEET = ROWS * COLS          # barcodes per sheet (28)
MARGIN_X = (A4_W - COLS * BC_W) // 2
MARGIN_Y = (A4_H - ROWS * BC_H) // 2


def load_font(size):
    for name in ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


FONT = load_font(FONT_SIZE)


def make_barcode(value):
    """Return a BC_W x BC_H image with a crisp Code128 barcode + number text."""
    modules = barcode.get("code128", str(value)).build()[0]  # string of 0/1
    quiet = 10                                               # quiet-zone modules
    total_modules = len(modules) + 2 * quiet
    module_w = max(1, (BC_W - 20) // total_modules)          # integer px per module
    bars_w = module_w * len(modules)

    img = Image.new("RGB", (BC_W, BC_H), "white")
    d = ImageDraw.Draw(img)

    x0 = (BC_W - bars_w) // 2
    top, bottom = 50, BC_H - 120
    for i, bit in enumerate(modules):
        if bit == "1":
            d.rectangle([x0 + i * module_w, top,
                         x0 + (i + 1) * module_w - 1, bottom], fill="black")

    text = str(value)
    tw = d.textlength(text, font=FONT)
    d.text(((BC_W - tw) / 2, bottom + 25), text, fill="black", font=FONT)

    if DRAW_BORDER:
        d.rectangle([0, 0, BC_W - 1, BC_H - 1], outline=(180, 180, 180), width=2)
    return img


def get_int(prompt):
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("Please enter a whole number.")


def main():
    start = get_int("Enter starting ID: ")
    end = get_int("Enter ending ID: ")
    if end < start:
        print("Ending ID must be >= starting ID.")
        sys.exit(1)

    ids = list(range(start, end + 1))
    total = len(ids)
    sheets = (total + PER_SHEET - 1) // PER_SHEET
    print(f"Generating {total} barcodes on {sheets} sheet(s) "
          f"({COLS} per row, {ROWS} rows, {PER_SHEET} per sheet)...")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for s in range(sheets):
        sheet = Image.new("RGB", (A4_W, A4_H), "white")
        chunk = ids[s * PER_SHEET:(s + 1) * PER_SHEET]
        for i, value in enumerate(chunk):
            r, c = divmod(i, COLS)
            sheet.paste(make_barcode(value),
                        (MARGIN_X + c * BC_W, MARGIN_Y + r * BC_H))
        path = os.path.join(OUTPUT_DIR, f"sheet_{s + 1}_{chunk[0]}-{chunk[-1]}.png")
        sheet.save(path, dpi=(300, 300))
        print("Saved", path)

    print("Done.")


if __name__ == "__main__":
    main()
