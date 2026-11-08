"""App icon, drawn in code so tray, window, shortcuts and the .exe share one design."""
ART = [
    "..##....##..",
    "..##....##..",
    ".##########.",
    "###.####.###",
    "############",
    "############",
    ".##......##.",
]
ROW_COLORS = [(255, 107, 74), (255, 107, 74), (255, 150, 70), (255, 200, 80), (120, 220, 255), (140, 140, 255),
              (200, 120, 255)]


def render(size=256):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = size * 0.22
    d.rounded_rectangle((0, 0, size - 1, size - 1), r, fill=(24, 25, 33, 255))
    cell = size / 16
    ox = (size - len(ART[0]) * cell) / 2
    oy = (size - len(ART) * cell) / 2
    for y, row in enumerate(ART):
        for x, ch in enumerate(row):
            if ch == "#":
                x0, y0 = ox + x * cell, oy + y * cell
                d.rectangle((x0 + cell * 0.08, y0 + cell * 0.08, x0 + cell * 0.92, y0 + cell * 0.92), fill=ROW_COLORS[y])
    return img


def save_ico(path):
    render(256).save(path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


if __name__ == "__main__":
    import os
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "ui", "icon.ico")
    save_ico(out)
    render(512).save(os.path.splitext(out)[0] + ".png")
    print("wrote", out)
