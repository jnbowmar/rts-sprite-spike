"""Procedural pixel-art sprites for the RTS spike.

Everything is drawn top-down at 1x, facing +x (right), light from the top-left.
Faction colors are one ramp swapped per team, so adding a faction is one line.
Run: .venv/bin/python sprites.py   -> writes game/art/*.png and preview.png
"""
import math
import random
from pathlib import Path

from PIL import Image

OUT = Path(__file__).parent / "game" / "art"

# Ramps run dark -> light. Index 0 shadow, 1 base, 2 lit, 3 highlight.
TEAMS = {
    "blue": [(28, 44, 86), (46, 78, 140), (74, 120, 190), (130, 175, 230)],
    "red": [(78, 24, 24), (140, 42, 38), (192, 70, 56), (236, 130, 100)],
}
OLIVE = [(44, 48, 30), (70, 76, 44), (100, 106, 62), (140, 146, 92)]
GUN = [(26, 26, 30), (52, 52, 58), (86, 86, 94), (130, 130, 140)]
SKIN = [(120, 78, 56), (170, 116, 84), (206, 152, 112), (230, 190, 150)]
GOLD = [(120, 90, 20), (200, 160, 50), (250, 220, 120), (255, 245, 200)]
CAPE = [(24, 24, 28), (40, 40, 46), (58, 58, 66), (84, 84, 94)]
LEAF = [(24, 52, 30), (38, 82, 42), (60, 118, 56), (104, 160, 80)]
SAND = [(96, 82, 56), (150, 130, 90), (190, 170, 120), (220, 205, 160)]
OUTLINE = (18, 20, 24, 255)


def canvas(w, h=None):
    return Image.new("RGBA", (w, h or w), (0, 0, 0, 0))


def put(img, x, y, c):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((int(x), int(y)), tuple(c) + (255,) if len(c) == 3 else c)


def light(nx, ny):
    """Ramp index from a surface normal, light from the top-left."""
    l = -(nx + ny) * 0.707
    return 3 if l > 0.55 else 2 if l > 0.1 else 1 if l > -0.45 else 0


def ellipse(img, cx, cy, rx, ry, ramp, flat=False):
    for y in range(img.height):
        for x in range(img.width):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if dx * dx + dy * dy <= 1:
                put(img, x, y, ramp[1] if flat else ramp[light(dx, dy)])


def rect(img, x0, y0, x1, y1, ramp):
    """Bevelled box: top/left edges lit, bottom/right edges shaded."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            i = 1
            if y == y0 or x == x0:
                i = 2
            if y == y1 or x == x1:
                i = 0
            put(img, x, y, ramp[i])


def outline(img):
    src = img.copy()
    for y in range(img.height):
        for x in range(img.width):
            if src.getpixel((x, y))[3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < img.width and 0 <= ny < img.height and src.getpixel((nx, ny))[3]:
                    img.putpixel((x, y), OUTLINE)
                    break
    return img


def strip(frames):
    w, h = frames[0].size
    sheet = canvas(w * len(frames), h)
    for i, f in enumerate(frames):
        sheet.paste(f, (i * w, 0))
    return sheet


# ---------- infantry (20x20, body centered at 10,10) ----------

def legs(img, team, off):
    for y0, o in ((7, off), (11, -off)):
        for y in (y0, y0 + 1):
            for x in range(9 + o, 12 + o):
                put(img, x, y, team[0])
        boot = 11 + o if o > 0 else 9 + o
        put(img, boot, y0, GUN[0])
        put(img, boot, y0 + 1, GUN[0])


def trooper(team, weapon, stride=0, recoil=0):
    img = canvas(20)
    legs(img, team, stride)
    if weapon == "rocket":
        rect(img, 6, 7, 8, 10, OLIVE)  # ammo pack
    else:
        rect(img, 6, 8, 8, 11, OLIVE)  # backpack
    ellipse(img, 10, 10, 2.8, 4.6, team)
    if weapon == "rifle":
        for x in range(11 - recoil, 18 - recoil):
            put(img, x, 12, GUN[2] if 13 <= x + recoil <= 15 else GUN[0])
        put(img, 13 - recoil, 11, team[1])
        put(img, 14 - recoil, 11, team[1])
        put(img, 12 - recoil, 11, SKIN[2])
        put(img, 15 - recoil, 11, SKIN[2])
    else:  # shoulder-fired tube over the right shoulder
        for x in range(7 - recoil, 17 - recoil):
            put(img, x, 12, OLIVE[2])
            put(img, x, 13, OLIVE[0])
        for y in (12, 13):
            put(img, 16 - recoil, y, GUN[0])
            put(img, 7 - recoil, y, GUN[1])
        put(img, 13 - recoil, 11, SKIN[2])
    ellipse(img, 10.6, 10, 1.8, 1.8, OLIVE)  # helmet
    return outline(img)


def hero(team, stride=0, recoil=0):
    img = canvas(22)
    ellipse(img, 8.5, 11, 4.5, 5.5, CAPE)
    for y0, o in ((8, stride), (12, -stride)):
        for y in (y0, y0 + 1):
            for x in range(10 + o, 13 + o):
                put(img, x, y, GUN[1])
    ellipse(img, 11, 11, 3.2, 4.6, team)
    put(img, 11, 6, GOLD[2])  # epaulettes
    put(img, 11, 15, GOLD[2])
    put(img, 12, 6, GOLD[1])
    put(img, 12, 15, GOLD[1])
    for x in range(12 - recoil, 17 - recoil):
        put(img, x, 14, GUN[0] if x + recoil != 14 else GUN[2])
    put(img, 13 - recoil, 13, SKIN[2])
    ellipse(img, 11.3, 11, 2.3, 2.3, SKIN)  # head
    for y in range(9, 14):  # beret, pushed to the back of the head
        for x in range(9, 12):
            if (x + 0.5 - 11.3) ** 2 + (y + 0.5 - 11) ** 2 <= 6:
                put(img, x, y, team[0] if x < 11 else team[1])
    put(img, 10, 10, GOLD[3])  # badge
    return outline(img)


# ---------- light tank (32x32 hull + separate rotating turret) ----------

def hull(team, tread=0):
    img = canvas(32)
    for y0 in (5, 22):
        for y in range(y0, y0 + 5):
            for x in range(3, 29):
                c = GUN[1] if (x + tread) % 3 == 0 else GUN[0]
                if y == y0:
                    c = GUN[2] if (x + tread) % 3 == 0 else GUN[1]
                put(img, x, y, c)
    rect(img, 5, 9, 26, 22, team)
    for y in range(10, 22):  # sloped glacis
        put(img, 25, y, team[2])
        put(img, 26, y, team[3] if y < 16 else team[2])
    for y in range(12, 20, 2):  # engine deck grille
        for x in range(6, 11):
            put(img, x, y, team[0])
    rect(img, 12, 9, 17, 10, OLIVE)  # stowage bins on the fenders
    rect(img, 12, 21, 17, 22, OLIVE)
    put(img, 27, 11, GOLD[3])  # headlights
    put(img, 27, 20, GOLD[3])
    return outline(img)


def turret(team, recoil=0):
    img = canvas(32)
    for x in range(20 - recoil, 30 - recoil):
        put(img, x, 15, GUN[2])
        put(img, x, 16, GUN[0])
    for y in range(14, 18):
        for x in range(28 - recoil, 31 - recoil):
            put(img, x, y, GUN[1] if y in (14, 17) else GUN[0])
    ellipse(img, 15, 16, 6.2, 5.6, team)
    ellipse(img, 13, 14, 1.8, 1.8, team[::-1][1:] + [team[0]], flat=True)
    put(img, 12, 13, team[3])
    put(img, 17, 19, GUN[0])  # coax mg port
    return outline(img)


# ---------- effects ----------

def explosion(i, n=8, size=28):
    rng = random.Random(7)  # same blob layout every frame so the cloud grows smoothly
    img = canvas(size)
    c = size / 2
    t = i / (n - 1)
    fire = [(255, 250, 220), (255, 214, 90), (240, 130, 40), (180, 60, 30)]
    smoke = [(40, 38, 36), (70, 66, 62), (100, 96, 90), (130, 126, 120)]
    for _ in range(9):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0, 5 + 7 * t)
        r = (3 + 5 * math.sin(min(t * 2.2, 1) * math.pi / 2)) * rng.uniform(0.6, 1.0)
        if t > 0.75:
            r *= 1 - (t - 0.75) * 2.5
        ramp = fire if t < 0.45 else smoke
        cx, cy = c + math.cos(a) * d, c + math.sin(a) * d
        for y in range(size):
            for x in range(size):
                dx, dy = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
                dd = dx * dx + dy * dy
                if dd > 1 or (t > 0.6 and (x + y + i) % 2 and dd > 0.5):
                    continue
                k = light(dx, dy)
                if ramp is fire:
                    k = 0 if dd < 0.25 - t * 0.4 else min(3, 1 + int(dd * 2 + t * 3))
                    put(img, x, y, fire[k])
                else:
                    put(img, x, y, smoke[k])
    return img


def flash(i):
    img = canvas(7)
    core = (255, 250, 220) if i == 0 else (255, 214, 90)
    for x in range(7):
        put(img, x, 3, (255, 214, 90))
    for y in range(1, 6):
        put(img, 3 + (i == 0), y, (255, 214, 90))
    put(img, 2, 3, core)
    put(img, 3, 3, core)
    return img


# ---------- props ----------

def tree(seed, size=26):
    rng = random.Random(seed)
    img = canvas(size)
    blobs = [(size / 2 + rng.uniform(-5, 5), size / 2 + rng.uniform(-5, 5), rng.uniform(4.5, 7)) for _ in range(6)]
    blobs.sort(key=lambda b: -(b[0] + b[1]))  # draw back-to-front toward the light
    for cx, cy, r in blobs:
        ellipse(img, cx, cy, r, r, LEAF)
    for _ in range(14):  # leaf speckle breaks up the flat shading
        x, y = rng.randrange(size), rng.randrange(size)
        if img.getpixel((x, y))[3]:
            put(img, x, y, LEAF[rng.choice((0, 3))])
    return outline(img)


def sandbags():
    img = canvas(30, 11)
    for row, y in enumerate((3, 7)):
        for k in range(4 + row):
            ellipse(img, 4 + k * 7 - row * 3.5, y, 3.6, 2.4, SAND)
    return outline(img)


def crater():
    img = canvas(18)
    for y in range(18):
        for x in range(18):
            d = math.hypot(x + 0.5 - 9, y + 0.5 - 9)
            if d < 4:
                put(img, x, y, (34, 28, 22))
            elif d < 6:
                put(img, x, y, (58, 46, 34))
            elif d < 8.2:
                n = light((x - 9) / d, (y - 9) / d)
                put(img, x, y, [(70, 56, 40), (92, 76, 54), (118, 98, 70), (140, 120, 88)][3 - n])
    return img


# ---------- terrain ----------

def noise(w, h, cell, seed):
    rng = random.Random(seed)
    gw, gh = w // cell + 2, h // cell + 2
    g = [[rng.random() for _ in range(gw)] for _ in range(gh)]

    def at(x, y):
        fx, fy = x / cell, y / cell
        x0, y0 = int(fx), int(fy)
        tx, ty = fx - x0, fy - y0
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a = g[y0][x0] + (g[y0][x0 + 1] - g[y0][x0]) * tx
        b = g[y0 + 1][x0] + (g[y0 + 1][x0 + 1] - g[y0 + 1][x0]) * tx
        return a + (b - a) * ty

    return at


def road_y(x):
    return 150 + 34 * math.sin(x / 95) + 12 * math.sin(x / 31)


def ground(w=480, h=270):
    img = Image.new("RGBA", (w, h))
    grass = [(52, 86, 44), (64, 102, 50), (78, 118, 58), (96, 136, 68)]
    dirt = [(92, 72, 48), (112, 90, 60), (132, 108, 74), (150, 126, 88)]
    big, small, noise_b = noise(w, h, 40, 1), noise(w, h, 9, 2), noise(w, h, 40, 5)
    rng = random.Random(3)
    for y in range(h):
        for x in range(w):
            v = big(x, y) * 0.7 + small(x, y) * 0.3
            dith = ((x + y) % 2) * 0.06  # 2px checker dither smooths the tone bands
            k = min(3, int((v + dith) * 4.2 - 0.6))
            c = grass[max(0, k)]
            dr = abs(y - road_y(x))
            if dr < 11 or (dr < 13 and (x * 7 + y * 3) % 5 == 0):
                c = dirt[1 + (small(x, y) > 0.55)]
                if 3 < dr < 5 and (x // 2) % 3:  # tire ruts
                    c = dirt[0]
            elif noise_b(x, y) > 0.78:  # dirt patches
                c = dirt[2] if small(x, y) > 0.45 else dirt[1]
            img.putpixel((x, y), c + (255,))
    for _ in range(900):  # grass blades
        x, y = rng.randrange(w), rng.randrange(h - 1)
        if abs(y - road_y(x)) > 13:
            img.putpixel((x, y), grass[3] + (255,))
            img.putpixel((x, y + 1), grass[0] + (255,))
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    walk = (4, 0, -4, 0)
    for name, ramp in TEAMS.items():
        for weapon in ("rifle", "rocket"):
            strip([trooper(ramp, weapon, s) for s in walk]).save(OUT / f"{weapon}_{name}_walk.png")
            strip([trooper(ramp, weapon, 0, r) for r in (0, 1)]).save(OUT / f"{weapon}_{name}_fire.png")
        strip([hero(ramp, s) for s in walk]).save(OUT / f"hero_{name}_walk.png")
        strip([hero(ramp, 0, r) for r in (0, 1)]).save(OUT / f"hero_{name}_fire.png")
        strip([hull(ramp, t) for t in range(3)]).save(OUT / f"tank_{name}_hull.png")
        strip([turret(ramp, r) for r in (0, 2)]).save(OUT / f"tank_{name}_turret.png")
    strip([explosion(i) for i in range(8)]).save(OUT / "explosion.png")
    strip([flash(i) for i in range(2)]).save(OUT / "flash.png")
    tree(11).save(OUT / "tree_a.png")
    tree(29).save(OUT / "tree_b.png")
    sandbags().save(OUT / "sandbags.png")
    crater().save(OUT / "crater.png")
    ground().save(OUT / "ground.png")
    preview()


def preview(scale=6):
    """Contact sheet of every sprite strip, scaled up on a dark background."""
    files = sorted(p for p in OUT.glob("*.png") if p.name != "ground.png")
    imgs = [Image.open(p) for p in files]
    pad = 4
    width = max(i.width for i in imgs) * scale + pad * 2
    height = sum(i.height * scale + pad for i in imgs) + pad
    sheet = Image.new("RGBA", (width, height), (30, 34, 30, 255))
    y = pad
    for im in imgs:
        big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        sheet.alpha_composite(big, (pad, y))
        y += big.height + pad
    sheet.save(Path(__file__).parent / "preview.png")


if __name__ == "__main__":
    main()
