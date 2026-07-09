from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 1200, 675
OUT = Path("output/images/geomdan_market_card_news_202606.png")

NAVY = "#18324a"
TEAL = "#147c78"
ORANGE = "#e38b29"
MUTED = "#6b7a86"
WHITE = "#ffffff"
INK = "#1f2b35"

FONT_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_REGULAR = "C:/Windows/Fonts/malgun.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (W, H), "#f6f8f7")
    draw = ImageDraw.Draw(image)

    for x in range(-200, W, 80):
        draw.line([(x, 0), (x + 350, H)], fill="#edf2f2", width=2)
    for y in range(40, H, 80):
        draw.line([(0, y), (W, y)], fill="#edf2f2", width=1)

    draw.rounded_rectangle([42, 38, W - 42, H - 38], radius=34, fill=WHITE, outline="#d9e3e2", width=2)

    draw.rounded_rectangle([86, 78, 306, 122], radius=22, fill="#e7f4f2")
    draw.text((110, 88), "실거래가 분석", fill=TEAL, font=font(24, True))

    draw.text((86, 150), "검단신도시 아파트", fill=NAVY, font=font(58, True))
    draw.text((86, 222), "원당동과 당하동은 따로 봐야 합니다", fill=INK, font=font(42, True))
    draw.text((88, 286), "2026년 5월 기준 | 인천 서구 검단권 매매·전세 흐름", fill=MUTED, font=font(24))

    cards = [
        ("매매 거래", "247건", "4월 316건보다 감소", TEAL),
        ("평균 매매가", "4.91억", "4월 4.73억에서 상승", ORANGE),
        ("전세가율", "65.4%", "매매가 먼저 움직임", NAVY),
    ]
    card_y = 360
    card_w = 318
    for i, (label, value, note, color) in enumerate(cards):
        x = 86 + i * (card_w + 28)
        draw.rounded_rectangle([x, card_y, x + card_w, card_y + 150], radius=24, fill="#fbfcfc", outline="#dbe5e4", width=2)
        draw.text((x + 28, card_y + 24), label, fill=MUTED, font=font(24, True))
        draw.text((x + 28, card_y + 58), value, fill=color, font=font(50, True))
        draw.text((x + 28, card_y + 116), note, fill=MUTED, font=font(20))

    draw.rounded_rectangle([86, 548, W - 86, 610], radius=22, fill=NAVY)
    draw.text(
        (118, 562),
        "핵심: 검단 평균보다 원당동 신축·당하동 거래량을 나눠 봐야 합니다",
        fill=WHITE,
        font=font(26, True),
    )

    base_x = 900
    for x, h, color in [(0, 140, "#dfe8e7"), (70, 180, "#cfdcdb"), (145, 120, "#e9efee")]:
        draw.rounded_rectangle([base_x + x, 120 + (180 - h), base_x + x + 58, 300], radius=8, fill=color)
        for wy in range(120 + (180 - h) + 20, 285, 28):
            draw.rectangle([base_x + x + 17, wy, base_x + x + 41, wy + 10], fill=WHITE)
    draw.line([860, 300, 1110, 300], fill="#cad7d6", width=5)

    for cx, cy, r, color in [(1030, 95, 9, ORANGE), (1080, 82, 6, TEAL), (838, 125, 5, NAVY)]:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    image.save(OUT, quality=95)
    print(OUT.resolve())


if __name__ == "__main__":
    main()
