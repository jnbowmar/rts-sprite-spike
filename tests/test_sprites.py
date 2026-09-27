import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import sprites  # noqa: E402

STRIPS = {
    "rifle_{t}_walk": (4, 20), "rifle_{t}_fire": (2, 20),
    "rocket_{t}_walk": (4, 20), "rocket_{t}_fire": (2, 20),
    "hero_{t}_walk": (4, 22), "hero_{t}_fire": (2, 22),
    "tank_{t}_hull": (3, 32), "tank_{t}_turret": (2, 32),
}


def generate(tmp_path, monkeypatch):
    monkeypatch.setattr(sprites, "OUT", tmp_path)
    monkeypatch.setattr(sprites, "preview", lambda: None)
    sprites.main()
    return tmp_path


def test_every_strip_has_the_frame_layout_godot_expects(tmp_path, monkeypatch):
    out = generate(tmp_path, monkeypatch)
    for team in sprites.TEAMS:
        for pattern, (frames, size) in STRIPS.items():
            img = Image.open(out / f"{pattern.format(t=team)}.png")
            assert img.size == (frames * size, size), pattern
    assert Image.open(out / "explosion.png").size == (8 * 28, 28)
    assert Image.open(out / "ground.png").size == (480, 270)


def test_factions_differ_only_in_color(tmp_path, monkeypatch):
    out = generate(tmp_path, monkeypatch)
    for pattern in STRIPS:
        blue = Image.open(out / f"{pattern.format(t='blue')}.png").getchannel("A")
        red = Image.open(out / f"{pattern.format(t='red')}.png").getchannel("A")
        assert blue.tobytes() == red.tobytes(), pattern


def test_committed_art_matches_the_generator(tmp_path, monkeypatch):
    out = generate(tmp_path, monkeypatch)
    committed = ROOT / "game" / "art"
    for png in sorted(out.glob("*.png")):
        fresh = Image.open(png).convert("RGBA").tobytes()
        saved = Image.open(committed / png.name).convert("RGBA").tobytes()
        assert fresh == saved, f"{png.name} is stale, rerun sprites.py"
