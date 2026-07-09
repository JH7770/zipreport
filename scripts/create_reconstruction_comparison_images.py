from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "images"
AGE_OUTPUT = OUT_DIR / "reconstruction_age_group_comparison_20260702.png"
COMPLEX_OUTPUT = OUT_DIR / "reconstruction_complex_examples_20260702.png"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    create_age_group_image()
    create_complex_examples_image()
    print(AGE_OUTPUT)
    print(COMPLEX_OUTPUT)


def create_age_group_image() -> None:
    image = Image.new("RGB", (1200, 675), "#f7f8fb")
    draw = ImageDraw.Draw(image)

    title = font(50, bold=True)
    subtitle = font(24)
    label = font(24, bold=True)
    small = font(20)
    value = font(28, bold=True)

    draw.rectangle((0, 0, 1200, 675), fill="#f7f8fb")
    draw.rounded_rectangle((46, 38, 1154, 620), radius=28, fill="#ffffff", outline="#d8dee8", width=2)

    draw.text((80, 66), "재건축 아파트, 신축보다 비쌀까?", font=title, fill="#19212f")
    draw.text((82, 126), "2026년 5월 서울 주요 지역 실거래가 연식군 비교", font=subtitle, fill="#556171")

    rows = [
        ("신축", "2021년 이후", 11.02, 5162, "#2f80ed"),
        ("준신축", "2011-2020년", 10.41, 4313, "#00a676"),
        ("30년 차 이상 구축", "1996년 이전", 11.48, 5263, "#d97706"),
    ]

    left_x = 96
    top_y = 215
    max_amount = 12.0
    max_pp = 5600

    draw.text((96, 176), "평균 거래금액", font=label, fill="#19212f")
    draw.text((620, 176), "3.3㎡당 평균 실거래가", font=label, fill="#19212f")

    for index, (name, desc, amount, pp, color) in enumerate(rows):
        y = top_y + index * 112
        draw.text((left_x, y), name, font=label, fill="#19212f")
        draw.text((left_x, y + 34), desc, font=small, fill="#667085")

        amount_x = 340
        amount_w = int(235 * (amount / max_amount))
        draw.rounded_rectangle((amount_x, y + 5, amount_x + 235, y + 41), radius=18, fill="#edf1f7")
        draw.rounded_rectangle((amount_x, y + 5, amount_x + amount_w, y + 41), radius=18, fill=color)
        draw.text((amount_x + 250, y + 4), f"{amount:.2f}억", font=value, fill="#19212f")

        pp_x = 720
        pp_w = int(255 * (pp / max_pp))
        draw.rounded_rectangle((pp_x, y + 5, pp_x + 255, y + 41), radius=18, fill="#edf1f7")
        draw.rounded_rectangle((pp_x, y + 5, pp_x + pp_w, y + 41), radius=18, fill=color)
        draw.text((pp_x + 270, y + 4), f"{pp:,}만 원", font=value, fill="#19212f")

    draw.rounded_rectangle((80, 550, 1120, 588), radius=18, fill="#172033")
    draw.text((106, 557), "단지의 새로움보다 입지와 미래 기대가 가격을 끌어올리는 구간이 있습니다.", font=small, fill="#ffffff")
    draw.text((82, 626), "자료: 국토교통부 아파트 매매 실거래가 API, ZipReport DB 집계", font=font(17), fill="#667085")

    image.save(AGE_OUTPUT, format="PNG", optimize=True)


def create_complex_examples_image() -> None:
    image = Image.new("RGB", (1200, 760), "#f7f8fb")
    draw = ImageDraw.Draw(image)

    title = font(46, bold=True)
    subtitle = font(23)
    label = font(23, bold=True)
    small = font(18)
    value = font(24, bold=True)

    draw.rounded_rectangle((46, 38, 1154, 705), radius=28, fill="#ffffff", outline="#d8dee8", width=2)
    draw.text((80, 66), "대표 단지로 보면 차이가 더 선명합니다", font=title, fill="#19212f")
    draw.text((82, 122), "2026년 5월 거래가 2건 이상 확인된 주요 단지의 3.3㎡당 평균 실거래가", font=subtitle, fill="#556171")

    rows = [
        ("목동", "목동신시가지7", "1986", 12002, "#d97706"),
        ("압구정", "현대14차", "1987", 22553, "#d97706"),
        ("여의도", "진주", "1977", 9440, "#d97706"),
        ("강동", "올림픽파크포레온", "2024", 12171, "#2f80ed"),
        ("강동", "고덕그라시움", "2019", 10207, "#00a676"),
    ]
    max_pp = 23000
    start_y = 205

    draw.text((90, 166), "생활권", font=small, fill="#667085")
    draw.text((205, 166), "단지", font=small, fill="#667085")
    draw.text((438, 166), "준공", font=small, fill="#667085")
    draw.text((548, 166), "3.3㎡당 평균", font=small, fill="#667085")

    for index, (area, complex_name, built, pp, color) in enumerate(rows):
        y = start_y + index * 88
        if index % 2 == 0:
            draw.rounded_rectangle((78, y - 18, 1122, y + 56), radius=14, fill="#f8fafc")
        draw.text((90, y), area, font=label, fill="#19212f")
        draw.text((205, y), complex_name, font=label, fill="#19212f")
        draw.text((438, y), f"{built}년", font=small, fill="#556171")

        bar_x = 548
        bar_w = int(390 * (pp / max_pp))
        draw.rounded_rectangle((bar_x, y + 2, bar_x + 390, y + 34), radius=16, fill="#edf1f7")
        draw.rounded_rectangle((bar_x, y + 2, bar_x + bar_w, y + 34), radius=16, fill=color)
        draw.text((960, y - 2), f"{pp:,}만 원", font=value, fill="#19212f")

    draw.rounded_rectangle((80, 640, 1120, 674), radius=16, fill="#172033")
    draw.text((104, 646), "같은 '재건축' 검색어라도 목동·압구정·여의도·강동의 가격 논리는 다릅니다.", font=small, fill="#ffffff")
    draw.text((82, 714), "자료: 국토교통부 아파트 매매 실거래가 API, ZipReport DB 집계", font=font(17), fill="#667085")

    image.save(COMPLEX_OUTPUT, format="PNG", optimize=True)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf"),
        Path("C:/Windows/Fonts/NanumGothicBold.ttf" if bold else "C:/Windows/Fonts/NanumGothic.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


if __name__ == "__main__":
    main()
