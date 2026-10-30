"""
Barcode sheet generator
-----------------------
Creates Code128 barcodes (613 x 452 px each) laid out 4 per row on
A4-sized images (2480 x 3508 px, 300 DPI).

Modes:
  1) Series          -> starting ID to ending ID
  2) Random          -> you type how many, then the numbers themselves
  3) Random + Series -> your random numbers first, then the series, line by line

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


# ---------------- INPUT HELPERS ----------------
def get_int(prompt, minimum=None):
    while True:
        try:
            n = int(input(prompt).strip())
        except ValueError:
            print("Please enter a whole number.")
            continue
        if minimum is not None and n < minimum:
            print(f"Please enter a number >= {minimum}.")
            continue
        return n


def get_series():
    """Ask for start and end, return list of IDs."""
    while True:
        start = get_int("Enter starting ID: ")
        end = get_int("Enter ending ID: ")
        if end < start:
            print("Ending ID must be >= starting ID. Try again.")
            continue
        return list(range(start, end + 1))


def get_random():
    """Ask how many, then ask for exactly that many numbers."""
    count = get_int("How many random numbers? ", minimum=1)
    while True:
        raw = input(f"Enter {count} random number(s) (space or comma separated): ")
        parts = raw.replace(",", " ").split()
        if len(parts) != count:
            print(f"You entered {len(parts)} number(s), but need exactly {count}. Try again.")
            continue
        if not all(p.isdigit() for p in parts):
            print("Only whole numbers (digits) are allowed. Try again.")
            continue
        return parts          # keep as strings so leading zeros are preserved


def choose_mode():
    print("\nChoose mode:")
    print("  1) Series            (starting ID to ending ID)")
    print("  2) Random            (you type the numbers)")
    print("  3) Random + Series   (random numbers first, then series)")
    while True:
        choice = input("Enter 1, 2 or 3: ").strip()
        if choice in ("1", "2", "3"):
            return choice
        print("Please enter 1, 2 or 3.")


# ---------------- OUTPUT ----------------
def build_sheets(ids):
    total = len(ids)
    sheets = (total + PER_SHEET - 1) // PER_SHEET
    print(f"\nGenerating {total} barcodes on {sheets} sheet(s) "
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


def main():
    mode = choose_mode()

    if mode == "1":
        ids = get_series()
    elif mode == "2":
        ids = get_random()
    else:
        series = get_series()
        randoms = get_random()
        ids = randoms + series        # random first, then series, one after another

    if not ids:
        print("Nothing to generate.")
        sys.exit(1)

    build_sheets(ids)


if __name__ == "__main__":
    main()
