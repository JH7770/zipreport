from __future__ import annotations

import binascii
from pathlib import Path
import struct
import zlib

from app.analyzers.apartment_analyzer import RegionReport
from app.config import PROJECT_ROOT
from app.generators.post_generator import format_money, format_percent

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - optional image feature.
    Image = None
    ImageDraw = None
    ImageFont = None


CANVAS_SIZE = (1200, 630)


def _create_vertical_gradient(width: int, height: int, start_color: str, end_color: str) -> Image.Image:
    r1, g1, b1 = int(start_color[1:3], 16), int(start_color[3:5], 16), int(start_color[5:7], 16)
    r2, g2, b2 = int(end_color[1:3], 16), int(end_color[3:5], 16), int(end_color[5:7], 16)
    
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        ratio = y / (height - 1)
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img


def create_monthly_report_image(
    report: RegionReport,
    lawd_cd: str,
    output_dir: Path | None = None,
) -> Path:
    directory = output_dir or PROJECT_ROOT / "output" / "images"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{report.deal_ym}_{lawd_cd}_featured.png"

    if Image is None or ImageDraw is None or ImageFont is None:
        _create_basic_report_png(report, path)
        return path

    # 1. Base gradient image (Indigo/Slate deep theme)
    image = _create_vertical_gradient(CANVAS_SIZE[0], CANVAS_SIZE[1], "#0b0f19", "#161f38")
    draw = ImageDraw.Draw(image)

    title_font = _load_font(44, bold=True)
    subtitle_font = _load_font(20, bold=True)
    metric_label_font = _load_font(18)
    metric_val_font = _load_font(28, bold=True)
    chart_label_font = _load_font(18, bold=True)
    card_label_font = _load_font(16)
    card_val_font = _load_font(22, bold=True)
    card_desc_font = _load_font(18)
    small_font = _load_font(16)

    # 2. Main card background (Outer glow-like border)
    draw.rounded_rectangle((40, 40, 1160, 590), radius=24, fill="#0f172a", outline="#1e293b", width=2)

    # 3. Header Title & Subtitle (Left aligned)
    year = report.deal_ym[:4]
    month = str(int(report.deal_ym[4:]))
    date_text = f"{year}년 {month}월 아파트 거래 동향"
    draw.text((70, 70), date_text, font=subtitle_font, fill="#60a5fa")

    region_title = f"{report.region_name} 실거래 리포트"
    draw.text((70, 105), region_title, font=title_font, fill="#f8fafc")

    # 4. Right side pill badge (Avg Price Change)
    rate = report.avg_change_rate or 0.0
    if rate > 0:
        badge_bg = "#064e3b"     # Emerald 900
        badge_border = "#059669" # Emerald 600
        badge_text_color = "#34d399" # Emerald 400
        badge_text = f"전월 대비 ▲ {rate:.1f}%"
    elif rate < 0:
        badge_bg = "#4c0519"     # Rose 950
        badge_border = "#e11d48" # Rose 600
        badge_text_color = "#fb7185" # Rose 400
        badge_text = f"전월 대비 ▼ {abs(rate):.1f}%"
    else:
        badge_bg = "#1e293b"     # Slate 800
        badge_border = "#475569" # Slate 600
        badge_text_color = "#94a3b8" # Slate 400
        badge_text = f"전월 대비 - {rate:.1f}%"

    badge_x1, badge_y1, badge_x2, badge_y2 = 870, 95, 1120, 145
    draw.rounded_rectangle((badge_x1, badge_y1, badge_x2, badge_y2), radius=15, fill=badge_bg, outline=badge_border, width=1)
    
    badge_w = badge_x2 - badge_x1
    text_w = _text_width(draw, badge_text, subtitle_font)
    text_x = badge_x1 + (badge_w - text_w) // 2
    draw.text((text_x, badge_y1 + 5), badge_text, font=subtitle_font, fill=badge_text_color)

    # 5. Key metrics section (3 columns)
    m_y1, m_y2 = 190, 290
    m_width = 320
    m_gap = 20
    m_start_x = 70

    metrics = [
        {"label": "거래 건수", "val": f"{report.total_count:,} 건", "color": "#f8fafc"},
        {"label": "거래량 변동", "val": format_percent(report.count_change_rate), "color": "#60a5fa"},
        {"label": "평균 거래가", "val": format_money(report.avg_deal_amount), "color": "#f8fafc"},
    ]

    for i, met in enumerate(metrics):
        x1 = m_start_x + i * (m_width + m_gap)
        x2 = x1 + m_width
        draw.rounded_rectangle((x1, m_y1, x2, m_y2), radius=12, fill="#1e293b", outline="#334155", width=1)
        draw.text((x1 + 20, m_y1 + 15), met["label"], font=metric_label_font, fill="#94a3b8")
        draw.text((x1 + 20, m_y1 + 45), met["val"], font=metric_val_font, fill=met["color"])

    # 6. Bottom half: Top Complexes Chart (Left) vs Highest Price Card (Right)
    # Left Half: Chart
    chart_x = 70
    chart_y = 325
    draw.text((chart_x, chart_y), "거래량 상위 단지", font=chart_label_font, fill="#94a3b8")

    top_items = report.top_volume_complexes[:5]
    max_count = max((item.trade_count for item in top_items), default=1)

    for index, item in enumerate(top_items):
        row_y = chart_y + 40 + index * 36
        label = f"{index + 1}. {item.apartment_name}"
        label_fit = _fit_text(draw, label, small_font, 350)
        draw.text((chart_x, row_y), label_fit, font=small_font, fill="#e2e8f0")

        count_label = f"{item.trade_count}건"
        draw.text((chart_x + 360, row_y), count_label, font=small_font, fill="#94a3b8")

        bar_track_x1 = chart_x + 400
        bar_track_x2 = chart_x + 600
        draw.rounded_rectangle((bar_track_x1, row_y + 6, bar_track_x2, row_y + 12), radius=3, fill="#1e293b")

        bar_w = int(200 * (item.trade_count / max_count))
        if bar_w > 0:
            draw.rounded_rectangle((bar_track_x1, row_y + 6, bar_track_x1 + bar_w, row_y + 12), radius=3, fill="#6366f1")

    # Right Half: Highest Price Card
    card_x1 = 730
    card_y1 = 335
    card_x2 = 1120
    card_y2 = 525

    draw.rounded_rectangle((card_x1, card_y1, card_x2, card_y2), radius=16, fill="#1e293b", outline="#d97706", width=1)
    draw.text((card_x1 + 25, card_y1 + 15), "최고 거래가 단지", font=card_label_font, fill="#f59e0b")

    if report.record_high_complexes:
        highest_item = report.record_high_complexes[0]
        apt_fit = _fit_text(draw, highest_item.apartment_name, card_val_font, 340)
        draw.text((card_x1 + 25, card_y1 + 45), apt_fit, font=card_val_font, fill="#f8fafc")
        price_str = format_money(highest_item.max_deal_amount)
        draw.text((card_x1 + 25, card_y1 + 80), price_str, font=metric_val_font, fill="#f8fafc")
        details = f"{highest_item.dong or ''} · 전용 {highest_item.exclusive_area_group or ''}"
        draw.text((card_x1 + 25, card_y1 + 125), details, font=card_desc_font, fill="#94a3b8")
    else:
        draw.text((card_x1 + 25, card_y1 + 45), "거래 정보가 없습니다.", font=card_desc_font, fill="#94a3b8")

    # 7. Footer Disclaimer
    footer_text = "국토교통부 실거래가 공개시스템 기준 • 본 자료는 참고용으로 투자 책임은 본인에게 있습니다."
    draw.text((70, 555), footer_text, font=small_font, fill="#475569")

    image.save(path, format="PNG", optimize=True)
    return path


def _create_basic_report_png(report: RegionReport, path: Path) -> None:
    width, height = CANVAS_SIZE
    pixels = bytearray(_rgb("#f7fafc") * width * height)
    _fill_rect(pixels, width, 54, 48, 1146, 582, _rgb("#ffffff"))
    _fill_rect(pixels, width, 54, 48, 1146, 160, _rgb("#1f5fbf"))
    _fill_rect(pixels, width, 92, 220, 420, 390, _rgb("#dbeafe"))
    _fill_rect(pixels, width, 452, 220, 780, 390, _rgb("#e0f2fe"))
    _fill_rect(pixels, width, 812, 220, 1080, 390, _rgb("#dcfce7" if (report.avg_change_rate or 0) >= 0 else "#fee2e2"))
    _draw_text(pixels, width, 92, 82, "APARTMENT REPORT", 7, _rgb("#ffffff"))
    _draw_text(pixels, width, 92, 220, f"{report.deal_ym[:4]}.{report.deal_ym[4:]}", 5, _rgb("#172033"))
    _draw_text(pixels, width, 92, 286, "TRADES", 4, _rgb("#5f6f86"))
    _draw_text(pixels, width, 92, 330, str(report.total_count), 7, _rgb("#172033"))
    _draw_text(pixels, width, 452, 286, "VOLUME", 4, _rgb("#5f6f86"))
    _draw_text(pixels, width, 452, 330, _ascii_percent(report.count_change_rate), 6, _rgb("#172033"))
    _draw_text(pixels, width, 812, 286, "AVG PRICE", 4, _rgb("#5f6f86"))
    _draw_text(pixels, width, 812, 330, _ascii_money(report.avg_deal_amount), 5, _rgb("#172033"))

    top_items = report.top_volume_complexes[:5]
    max_count = max((item.trade_count for item in top_items), default=1)
    for index, item in enumerate(top_items):
        y = 445 + index * 30
        bar_width = int(760 * (item.trade_count / max_count))
        _fill_rect(pixels, width, 92, y, 92 + bar_width, y + 18, _rgb("#3b82f6"))

    _write_png(path, width, height, bytes(pixels))


def _fill_rect(pixels: bytearray, width: int, left: int, top: int, right: int, bottom: int, color: bytes) -> None:
    for y in range(max(top, 0), min(bottom, CANVAS_SIZE[1])):
        row_start = (y * width + max(left, 0)) * 3
        row_end = (y * width + min(right, width)) * 3
        pixels[row_start:row_end] = color * ((row_end - row_start) // 3)


def _write_png(path: Path, width: int, height: int, rgb: bytes) -> None:
    scanlines = bytearray()
    stride = width * 3
    for y in range(height):
        scanlines.append(0)
        scanlines.extend(rgb[y * stride : (y + 1) * stride])

    def chunk(kind: bytes, data: bytes) -> bytes:
        checksum = binascii.crc32(kind + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(scanlines), level=9))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def _rgb(hex_color: str) -> bytes:
    value = hex_color.lstrip("#")
    return bytes(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _ascii_money(value: int | None) -> str:
    if value is None:
        return "-"
    return f"{value / 100000000:.1f}EOK"


def _ascii_percent(value: float | None) -> str:
    if value is None:
        return "-"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}%"


def _draw_text(pixels: bytearray, width: int, x: int, y: int, text: str, scale: int, color: bytes) -> None:
    cursor = x
    for char in text.upper():
        pattern = _FONT.get(char, _FONT[" "])
        for row_index, row in enumerate(pattern):
            for col_index, cell in enumerate(row):
                if cell == "1":
                    _fill_rect(
                        pixels,
                        width,
                        cursor + col_index * scale,
                        y + row_index * scale,
                        cursor + (col_index + 1) * scale,
                        y + (row_index + 1) * scale,
                        color,
                    )
        cursor += 6 * scale


_FONT = {
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "%": ["11001", "11010", "00100", "01000", "10110", "00110", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
}


def _metric(draw: ImageDraw.ImageDraw, position: tuple[int, int], label: str, value: str, body_font: object, value_font: object) -> None:
    x, y = position
    draw.text((x, y), label, font=body_font, fill="#5f6f86")
    draw.text((x, y + 38), value, font=value_font, fill="#172033")


def _load_font(size: int, bold: bool = False) -> object:
    candidates = [
        # Windows
        "C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/NanumGothicBold.ttf" if bold else "C:/Windows/Fonts/NanumGothic.ttf",
        # Ubuntu/Linux Nanum Fonts
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf" if bold else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/nanum/NanumGothicBold.ttf" if bold else "/usr/share/fonts/nanum/NanumGothic.ttf",
        # macOS SD Gothic
        "/System/Library/Fonts/AppleSDGothicNeo.ttc" if bold else "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        # Windows Standard Fallbacks
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size=size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def _fit_text(draw: ImageDraw.ImageDraw, text: str, font: object, max_width: int) -> str:
    if _text_width(draw, text, font) <= max_width:
        return text
    suffix = "..."
    trimmed = text
    while trimmed and _text_width(draw, trimmed + suffix, font) > max_width:
        trimmed = trimmed[:-1]
    return trimmed + suffix


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: object) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]
