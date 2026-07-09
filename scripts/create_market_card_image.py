from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "images" / "202605_11500_sale_jeonse_card.png"
SIZE = (1200, 630)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", SIZE, "#f5f7fb")
    draw = ImageDraw.Draw(image)

    title_font = font(58, bold=True)
    subtitle_font = font(30, bold=True)
    label_font = font(23)
    value_font = font(42, bold=True)
    note_font = font(26, bold=True)
    source_font = font(17)

    draw.rounded_rectangle((42, 38, 1158, 592), radius=26, fill="#ffffff", outline="#d7dde8", width=2)
    draw.rounded_rectangle((42, 38, 1158, 166), radius=26, fill="#16324f")
    draw.rectangle((42, 110, 1158, 166), fill="#16324f")

    draw.text((78, 62), "강서구 아파트 시장", font=title_font, fill="#ffffff")
    draw.text((78, 121), "매매가는 올랐는데, 전세는 왜 덜 따라올까?", font=subtitle_font, fill="#dbeafe")

    badge_text = "2026년 5월 실거래 기준"
    badge_w = text_width(draw, badge_text, label_font) + 36
    draw.rounded_rectangle((1158 - badge_w - 50, 74, 1108, 120), radius=18, fill="#f4b942")
    draw.text((1158 - badge_w - 32, 82), badge_text, font=label_font, fill="#172033")

    metrics = [
        ("평균 매매가", "9.2억", "전월 대비 +5.4%", "#e8f1ff", "#1f5fbf"),
        ("평균 전세보증금", "5.0억", "전월 대비 +3.0%", "#ecfdf3", "#137a3f"),
        ("전세가율", "54.0%", "매매가 대비 전세", "#fff7e6", "#b45f06"),
        ("매매 거래량", "425건", "전월 대비 -30.1%", "#f3ecff", "#6d3fc0"),
    ]

    card_w = 258
    card_h = 154
    gap = 22
    start_x = 78
    y = 210
    for index, (label, value, desc, bg, color) in enumerate(metrics):
        x = start_x + index * (card_w + gap)
        draw.rounded_rectangle((x, y, x + card_w, y + card_h), radius=18, fill=bg, outline="#d7dde8", width=1)
        draw.text((x + 22, y + 22), label, font=label_font, fill="#536276")
        draw.text((x + 22, y + 56), value, font=value_font, fill=color)
        draw.text((x + 22, y + 112), desc, font=source_font, fill="#536276")

    draw.rounded_rectangle((78, 410, 1122, 510), radius=20, fill="#172033")
    key = "거래는 줄었는데, 체결된 매매의 가격대가 높아진 달"
    draw.text((112, 430), key, font=note_font, fill="#ffffff")
    draw.text((112, 468), "마곡 등 선호 생활권 거래가 평균가를 끌어올렸을 가능성", font=label_font, fill="#cbd5e1")

    source = "자료: 국토교통부 실거래가, 한국부동산원 R-ONE 월간 가격지수"
    draw.text((78, 548), source, font=source_font, fill="#667085")

    image.save(OUTPUT, format="PNG", optimize=True)
    print(OUTPUT)


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
