from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "images" / "the-sharp-geomdan-lakepark-subscription-4050.png"
SIZE = (1200, 630)

NAVY = "#16324f"
TEAL = "#147c78"
ORANGE = "#e38b29"
GREEN = "#2f7d59"
INK = "#172033"
MUTED = "#667085"
BG = "#f5f8f7"
WHITE = "#ffffff"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", SIZE, BG)
    draw = ImageDraw.Draw(image)

    title_font = font(54, True)
    sub_font = font(30, True)
    badge_font = font(23, True)
    label_font = font(24, True)
    value_font = font(42, True)
    small_font = font(20)
    bottom_font = font(28, True)

    draw_background(draw)

    draw.rounded_rectangle((46, 38, 1154, 592), radius=28, fill=WHITE, outline="#d9e4e3", width=2)
    draw.rounded_rectangle((46, 38, 1154, 176), radius=28, fill=NAVY)
    draw.rectangle((46, 115, 1154, 176), fill=NAVY)

    draw.text((82, 60), "더샵 검단레이크파크", font=title_font, fill=WHITE)
    draw.text((86, 126), "청약 일정표 | 40·50대 자금·규제 체크", font=sub_font, fill="#dbeafe")

    draw_badge(draw, (890, 72), "특공 6.24", TEAL, badge_font)
    draw_badge(draw, (1022, 72), "1순위 6.25", ORANGE, badge_font)

    metrics = [
        ("일반공급", "가점 40%", "추첨 60%", TEAL),
        ("84A 최고가", "6.63억", "계약금 10%", ORANGE),
        ("핵심 규제", "전매 3년", "거주의무 3년", NAVY),
    ]
    x0, y0 = 82, 226
    card_w, card_h, gap = 326, 164, 28
    for index, (label, value, note, color) in enumerate(metrics):
        x = x0 + index * (card_w + gap)
        draw.rounded_rectangle((x, y0, x + card_w, y0 + card_h), radius=22, fill="#fbfcfc", outline="#dbe5e4", width=2)
        draw.text((x + 28, y0 + 24), label, font=label_font, fill=MUTED)
        draw.text((x + 28, y0 + 62), value, font=value_font, fill=color)
        draw.text((x + 28, y0 + 118), note, font=small_font, fill=INK)

    draw.rounded_rectangle((82, 430, 1118, 514), radius=22, fill="#eef6f4", outline="#cfe3df", width=2)
    draw.text((116, 448), "정당계약 7.14~7.18  |  중도금 이자후불제  |  스트레스 DSR 체크", font=bottom_font, fill=GREEN)

    draw.text((86, 550), "자료 기준: 더샵 검단레이크파크 공식 홈페이지·입주자모집공고", font=small_font, fill=MUTED)

    image.save(OUTPUT, format="PNG", optimize=True)
    print(OUTPUT.resolve())


def draw_background(draw: ImageDraw.ImageDraw) -> None:
    for x in range(-220, SIZE[0], 82):
        draw.line((x, 0, x + 360, SIZE[1]), fill="#e8efee", width=2)
    for y in range(40, SIZE[1], 90):
        draw.line((0, y, SIZE[0], y), fill="#e8efee", width=1)

    draw.ellipse((902, 392, 1150, 640), fill="#d9ece7")
    draw.arc((920, 410, 1128, 618), start=190, end=340, fill=TEAL, width=6)
    draw.arc((960, 448, 1088, 576), start=190, end=340, fill=ORANGE, width=5)


def draw_badge(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    color: str,
    font_obj: ImageFont.FreeTypeFont,
) -> None:
    x, y = xy
    width = text_width(draw, text, font_obj) + 34
    draw.rounded_rectangle((x, y, x + width, y + 46), radius=20, fill=color)
    draw.text((x + 17, y + 8), text, font=font_obj, fill=WHITE)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf"),
        Path("C:/Windows/Fonts/NanumGothicBold.ttf" if bold else "C:/Windows/Fonts/NanumGothic.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def text_width(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.ImageFont) -> int:
    box = draw.textbbox((0, 0), text, font=font_obj)
    return box[2] - box[0]


if __name__ == "__main__":
    main()
