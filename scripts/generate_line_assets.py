#!/usr/bin/env python3
"""Generate deterministic LINE assets for Meisiru.

Dependencies:
    python -m pip install Pillow qrcode opencv-python-headless

The rich menu is rendered from primitives and text.  The two printed-card
assets keep their existing pixels and receive a QR-only patch for the
production LINE URL.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import qrcode
from PIL import Image, ImageChops, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_H


ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
LINE_URL = "https://lin.ee/rxtsy4f"

RICHMENU_SIZE = (2500, 1686)
CARD_SIZE = (1456, 880)

NAVY = "#0B2342"
NAVY_DEEP = "#071A32"
NAVY_SOFT = "#123557"
TEAL = "#00A875"
TEAL_DARK = "#00856B"
YELLOW = "#FFD84D"
WHITE = "#FFFFFF"
MIST = "#EAF4F2"


@dataclass(frozen=True)
class QRPatch:
    filename: str
    top_left: tuple[int, int]
    box_size: int


QR_PATCHES = (
    # 29 data modules + 4-module quiet zone on each side = 37 modules.
    QRPatch("card_back.png", (1044, 255), 8),   # 296 x 296
    QRPatch("tri_b1.png", (975, 207), 10),     # 370 x 370
)


def font_path() -> Path:
    candidates = (
        Path(r"C:\Windows\Fonts\BIZ-UDGothicB.ttc"),
        Path(r"C:\Windows\Fonts\YuGothB.ttc"),
        Path(r"C:\Windows\Fonts\NotoSansJP-VF.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansJP-Bold.ttf"),
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Japanese bold font not found. Install Noto Sans JP or BIZ UDPGothic."
    )


FONT_PATH = font_path()


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size)


def centered_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    size: int,
    fill: str,
    *,
    stroke_width: int = 0,
    stroke_fill: str | None = None,
) -> None:
    draw.text(
        xy,
        text,
        font=font(size),
        fill=fill,
        anchor="mm",
        align="center",
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )


def pill(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    text: str,
    *,
    background: str,
    foreground: str,
    width: int,
) -> None:
    cx, cy = center
    height = 70
    draw.rounded_rectangle(
        (cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2),
        radius=height // 2,
        fill=background,
    )
    centered_text(draw, center, text, 38, foreground)


def draw_arrow_button(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    *,
    foreground: str,
    background: str,
) -> None:
    cx, cy = center
    r = 34
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=background)
    draw.line((cx - 8, cy - 14, cx + 8, cy, cx - 8, cy + 14), fill=foreground, width=10, joint="curve")


def icon_document(draw: ImageDraw.ImageDraw, cx: int, cy: int, color: str, accent: str) -> None:
    draw.rounded_rectangle((cx - 82, cy - 100, cx + 58, cy + 86), radius=18, outline=color, width=16)
    draw.polygon(((cx + 10, cy - 100), (cx + 58, cy - 52), (cx + 10, cy - 52)), fill=accent)
    draw.line((cx - 47, cy - 25, cx + 22, cy - 25), fill=color, width=14)
    draw.line((cx - 47, cy + 12, cx + 22, cy + 12), fill=color, width=14)
    draw.line((cx - 47, cy + 49, cx - 6, cy + 49), fill=color, width=14)
    draw.line((cx + 90, cy - 8, cx + 90, cy + 76), fill=accent, width=18)
    draw.line((cx + 58, cy + 44, cx + 90, cy + 76, cx + 122, cy + 44), fill=accent, width=18, joint="curve")


def icon_card_search(draw: ImageDraw.ImageDraw, cx: int, cy: int, color: str, accent: str) -> None:
    draw.rounded_rectangle((cx - 125, cy - 72, cx + 70, cy + 58), radius=20, outline=color, width=16)
    draw.ellipse((cx - 88, cy - 36, cx - 44, cy + 8), fill=accent)
    draw.line((cx - 26, cy - 27, cx + 32, cy - 27), fill=color, width=13)
    draw.line((cx - 26, cy + 8, cx + 16, cy + 8), fill=color, width=13)
    draw.ellipse((cx + 39, cy + 19, cx + 119, cy + 99), outline=accent, width=17)
    draw.line((cx + 96, cy + 76, cx + 134, cy + 114), fill=accent, width=18)


def icon_services(draw: ImageDraw.ImageDraw, cx: int, cy: int, color: str, accent: str) -> None:
    size = 72
    gap = 22
    for row in range(2):
        for col in range(2):
            x0 = cx - size - gap // 2 + col * (size + gap)
            y0 = cy - size - gap // 2 + row * (size + gap)
            fill = accent if (row, col) == (0, 0) else None
            draw.rounded_rectangle((x0, y0, x0 + size, y0 + size), radius=16, fill=fill, outline=color, width=13)


def icon_yen(draw: ImageDraw.ImageDraw, cx: int, cy: int, color: str, accent: str) -> None:
    draw.ellipse((cx - 105, cy - 105, cx + 105, cy + 105), outline=color, width=16)
    centered_text(draw, (cx, cy - 2), "¥", 132, accent)


def icon_flow(draw: ImageDraw.ImageDraw, cx: int, cy: int, color: str, accent: str) -> None:
    xs = (cx - 105, cx, cx + 105)
    for i, x in enumerate(xs):
        fill = accent if i == 0 else None
        draw.ellipse((x - 34, cy - 34, x + 34, cy + 34), fill=fill, outline=color, width=13)
        if i < 2:
            draw.line((x + 42, cy, xs[i + 1] - 48, cy), fill=color, width=13)
            draw.line((xs[i + 1] - 62, cy - 15, xs[i + 1] - 47, cy, xs[i + 1] - 62, cy + 15), fill=color, width=11, joint="curve")


def icon_faq(draw: ImageDraw.ImageDraw, cx: int, cy: int, color: str, accent: str) -> None:
    draw.rounded_rectangle((cx - 115, cy - 83, cx + 76, cy + 58), radius=28, outline=color, width=15)
    draw.polygon(((cx - 63, cy + 57), (cx - 94, cy + 98), (cx - 28, cy + 58)), fill=color)
    centered_text(draw, (cx - 17, cy - 13), "?", 122, accent)


IconDrawer = Callable[[ImageDraw.ImageDraw, int, int, str, str], None]


@dataclass(frozen=True)
class Tile:
    box: tuple[int, int, int, int]
    background: str
    foreground: str
    accent: str
    eyebrow: str
    title_lines: tuple[str, ...]
    icon: IconDrawer
    pill_background: str
    pill_foreground: str


def draw_tile(draw: ImageDraw.ImageDraw, tile: Tile) -> None:
    x0, y0, x1, y1 = tile.box
    cx = (x0 + x1) // 2
    local_top = y0
    draw.rectangle(tile.box, fill=tile.background)

    pill(
        draw,
        (cx, local_top + 92),
        tile.eyebrow,
        background=tile.pill_background,
        foreground=tile.pill_foreground,
        width=320,
    )
    tile.icon(draw, cx, local_top + 285, tile.foreground, tile.accent)

    if len(tile.title_lines) == 1:
        centered_text(draw, (cx, local_top + 575), tile.title_lines[0], 94, tile.foreground)
    else:
        centered_text(draw, (cx, local_top + 530), tile.title_lines[0], 98, tile.foreground)
        centered_text(draw, (cx, local_top + 650), tile.title_lines[1], 86, tile.foreground)

    draw_arrow_button(
        draw,
        (x1 - 76, y1 - 76),
        foreground=tile.background,
        background=tile.accent,
    )


def generate_richmenu(path: Path) -> None:
    image = Image.new("RGB", RICHMENU_SIZE, NAVY_DEEP)
    draw = ImageDraw.Draw(image)
    x = (0, 833, 1667, 2500)
    y = (0, 843, 1686)

    tiles = (
        Tile((x[0], y[0], x[1], y[1]), YELLOW, NAVY, TEAL_DARK, "登録後すぐ届く", ("無料", "テンプレート"), icon_document, NAVY, WHITE),
        Tile((x[1], y[0], x[2], y[1]), TEAL_DARK, WHITE, YELLOW, "名刺写真でOK", ("名刺を", "見てもらう"), icon_card_search, NAVY, WHITE),
        Tile((x[2], y[0], x[3], y[1]), NAVY, WHITE, TEAL, "できること", ("サービス", "内容"), icon_services, TEAL, NAVY_DEEP),
        Tile((x[0], y[1], x[1], y[2]), NAVY_SOFT, WHITE, YELLOW, "5万円〜", ("料金の目安",), icon_yen, TEAL_DARK, WHITE),
        Tile((x[1], y[1], x[2], y[2]), "#0B3C53", WHITE, YELLOW, "5ステップ", ("制作の流れ",), icon_flow, TEAL, NAVY_DEEP),
        Tile((x[2], y[1], x[3], y[2]), NAVY_DEEP, WHITE, TEAL, "不安を解消", ("よくある質問",), icon_faq, YELLOW, NAVY),
    )
    for tile in tiles:
        draw_tile(draw, tile)

    # Exact thirds remain visually obvious when LINE overlays six tap areas.
    divider = 10
    draw.rectangle((x[1] - divider // 2, 0, x[1] + divider // 2, y[2]), fill=NAVY_DEEP)
    draw.rectangle((x[2] - divider // 2, 0, x[2] + divider // 2, y[2]), fill=NAVY_DEEP)
    draw.rectangle((0, y[1] - divider // 2, x[3], y[1] + divider // 2), fill=NAVY_DEEP)
    draw.rectangle((0, 0, x[3] - 1, y[2] - 1), outline=NAVY_DEEP, width=10)

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", compress_level=9, optimize=False)


def make_qr(box_size: int) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=box_size,
        border=4,
    )
    qr.add_data(LINE_URL)
    qr.make(fit=True)
    if qr.version != 3 or qr.modules_count != 29:
        raise RuntimeError(
            f"Unexpected QR geometry: version={qr.version}, modules={qr.modules_count}"
        )
    return qr.make_image(fill_color=NAVY, back_color=WHITE).convert("RGB")


def replace_qr(path: Path, patch: QRPatch) -> None:
    original = Image.open(path).convert("RGB")
    if original.size != CARD_SIZE:
        raise ValueError(f"{path.name}: expected {CARD_SIZE}, got {original.size}")

    qr = make_qr(patch.box_size)
    updated = original.copy()
    updated.paste(qr, patch.top_left)

    changed = ImageChops.difference(original, updated).getbbox()
    if changed:
        x, y = patch.top_left
        allowed = (x, y, x + qr.width, y + qr.height)
        if not (
            allowed[0] <= changed[0]
            and allowed[1] <= changed[1]
            and changed[2] <= allowed[2]
            and changed[3] <= allowed[3]
        ):
            raise AssertionError(f"{path.name}: pixels changed outside QR patch")

    updated.save(path, format="PNG", compress_level=9, optimize=False)


def decode_qr(path: Path) -> str:
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV is required for final QR validation. "
            "Install opencv-python-headless."
        ) from exc

    # cv2.imread does not reliably accept non-ASCII Windows paths.
    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"OpenCV could not read {path}")
    value, points, _ = cv2.QRCodeDetector().detectAndDecode(image)
    if points is None or not value:
        raise RuntimeError(f"OpenCV could not decode QR from {path.name}")
    return value


def validate_assets() -> None:
    expected = {
        "richmenu_2500x1686.png": RICHMENU_SIZE,
        "card_back.png": CARD_SIZE,
        "tri_b1.png": CARD_SIZE,
    }
    for filename, size in expected.items():
        with Image.open(ASSETS / filename) as image:
            if image.size != size:
                raise AssertionError(f"{filename}: expected {size}, got {image.size}")
            print(f"OK size   {filename}: {image.size[0]}x{image.size[1]}")

    for patch in QR_PATCHES:
        decoded = decode_qr(ASSETS / patch.filename)
        if decoded != LINE_URL:
            raise AssertionError(
                f"{patch.filename}: decoded {decoded!r}, expected {LINE_URL!r}"
            )
        print(f"OK QR     {patch.filename}: {decoded}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Do not regenerate; only validate dimensions and QR decode results.",
    )
    args = parser.parse_args()

    if not args.verify_only:
        generate_richmenu(ASSETS / "richmenu_2500x1686.png")
        for patch in QR_PATCHES:
            replace_qr(ASSETS / patch.filename, patch)

    validate_assets()


if __name__ == "__main__":
    main()
