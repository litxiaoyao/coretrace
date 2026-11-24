#!/usr/bin/env python3
"""Wrap the two supplied conceptual PNGs in font-free PDF containers.

This only embeds the existing generated image bytes at the publication width;
it does not edit, redraw, resample, or regenerate their visual content.
Requires PyMuPDF and Pillow. Run from any working directory after placing the
supplied PNGs in paper/figures/.
"""
from pathlib import Path
from io import BytesIO

import fitz
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
WIDTH_PT = 6.75 * 72


def wrap(stem: str) -> None:
    png = ROOT / "paper" / "figures" / f"{stem}.png"
    pdf = png.with_suffix(".pdf")
    with Image.open(png) as im:
        width, height = im.size
        expected = im.convert("RGB").tobytes()
    doc = fitz.open()
    page = doc.new_page(width=WIDTH_PT, height=WIDTH_PT * height / width)
    page.insert_image(page.rect, filename=str(png))
    doc.save(pdf, garbage=4, deflate=True)
    doc.close()
    with fitz.open(pdf) as checked:
        page = checked[0]
        assert not page.get_fonts(), "A pure-image PDF should contain no font resources"
        images = page.get_images(full=True)
        assert len(images) == 1
        embedded = checked.extract_image(images[0][0])["image"]
        with Image.open(BytesIO(embedded)) as im:
            assert im.size == (width, height)
            assert im.convert("RGB").tobytes() == expected
    print(f"Wrapped {png.name}: original RGB pixels preserved, no font resources")


if __name__ == "__main__":
    for stem in ("figure1_teaser", "figure2_method"):
        wrap(stem)
