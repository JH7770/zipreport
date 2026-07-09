from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 1200, 720
OUT = Path("output/images/geomdan_wondang_dangha_compare_202606.png")

NAVY = "#18324a"
TEAL = "#147c78"
ORANGE = "#e38b29"
MUTED = "#667785"
BG = "#f7faf9"
WHITE = "#ffffff"
LINE = "#d9e5e3"

FONT_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_REGULAR = "C:/Windows/Fonts/malgun.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle([56, 46, W - 56, H - 46], radius=34, fill=WHITE, outline=LINE, width=2)
    draw.text((92, 86), "검단신도시 동별 실거래 비교", fill=NAVY, font=font(44, True))
    draw.text((94, 146), "2026년 5월 기준 | 원당동은 가격, 당하동은 거래량", fill=MUTED, font=font(25))

    # Divider
    draw.line([600, 210, 600, 560], fill=LINE, width=3)

    # Wondang
    draw.rounded_rectangle([92, 220, 548, 560], radius=26, fill="#f9fcfc", outline="#dbe8e6", width=2)
    draw.text((132, 258), "원당동", fill=TEAL, font=font(44, True))
    draw.text((132, 326), "86건", fill=NAVY, font=font(62, True))
    draw.text((286, 346), "매매 거래", fill=MUTED, font=font(24, True))
    draw.text((132, 420), "평균 매매가", fill=MUTED, font=font(26, True))
    draw.text((132, 456), "6억 3,434만 원", fill=TEAL, font=font(40, True))
    draw.text((132, 516), "신축 인기 단지 중심", fill=MUTED, font=font(23))

    # Dangha
    draw.rounded_rectangle([652, 220, 1108, 560], radius=26, fill="#fffdf9", outline="#e8dfd2", width=2)
    draw.text((692, 258), "당하동", fill=ORANGE, font=font(44, True))
    draw.text((692, 326), "99건", fill=NAVY, font=font(62, True))
    draw.text((846, 346), "매매 거래", fill=MUTED, font=font(24, True))
    draw.text((692, 420), "평균 매매가", fill=MUTED, font=font(26, True))
    draw.text((692, 456), "4억 7,526만 원", fill=ORANGE, font=font(40, True))
    draw.text((692, 516), "선택지 넓은 실수요 구간", fill=MUTED, font=font(23))

    draw.rounded_rectangle([92, 600, W - 92, 654], radius=20, fill=NAVY)
    draw.text((128, 612), "검단 평균 하나로 판단하면 단지별 온도 차이를 놓칠 수 있습니다", fill=WHITE, font=font(25, True))

    image.save(OUT, quality=95)
    print(OUT.resolve())


if __name__ == "__main__":
    main()
