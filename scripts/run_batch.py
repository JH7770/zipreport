from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.analyzers.apartment_analyzer import analyze_month, persist_monthly_stats
from app.collectors.molit_trade_collector import MolitTradeCollector
from app.config import REGIONS, PROJECT_ROOT, get_settings
from app.db.database import connect, initialize, insert_trades, save_wordpress_post
from app.generators.post_generator import (
    render_apartment_detail_report,
    render_monthly_report,
    render_top_rising_report,
    write_markdown,
    write_report,
)
from app.generators.llm_writer import LlmRewriteConfig, rewrite_markdown_with_llm
from app.generators.report_image import create_monthly_report_image
from app.publishers.wordpress_publisher import WordpressPublisher, extract_title
from app.quality.content_audit import audit_markdown_file, format_audit_result


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect, analyze, and generate apartment reports.")
    parser.add_argument("--deal-ym", required=True, help="계약년월 YYYYMM")
    parser.add_argument("--lawd-cd", action="append", help="대상 지역 코드. 여러 번 지정 가능")
    parser.add_argument("--skip-collect", action="store_true", help="API 수집 없이 DB에 있는 데이터로만 생성")
    parser.add_argument("--publish", action="store_true", help="생성한 Markdown을 WordPress draft로 발행")
    parser.add_argument("--status", help="WordPress post status. 기본값은 DEFAULT_STATUS")
    parser.add_argument("--category", action="append", type=int, default=[], help="WordPress category ID")
    parser.add_argument("--tag", action="append", type=int, default=[], help="WordPress tag ID")
    parser.add_argument("--use-llm", action="store_true", help="Rewrite generated Markdown with an LLM.")
    parser.add_argument("--featured-image", type=Path, help="Image path to upload as the WordPress featured image.")
    parser.add_argument("--generate-image", action="store_true", help="Generate a featured image for each region.")
    parser.add_argument("--skip-audit", action="store_true", help="Skip generated Markdown quality audit.")
    args = parser.parse_args()

    settings = get_settings()
    conn = connect(settings.database_path)
    initialize(conn)
    log_path = PROJECT_ROOT / "logs" / "batch.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    lawd_codes = args.lawd_cd or list(REGIONS.keys())
    collector = None
    if not args.skip_collect:
        collector = MolitTradeCollector(settings.public_data_api_key)
    publisher = None
    if args.publish:
        publisher = WordpressPublisher(
            settings.wordpress_url,
            settings.wordpress_username,
            settings.wordpress_app_password,
        )

    all_generated: list[Path] = []
    for lawd_cd in lawd_codes:
        generated: list[Path] = []
        _log(log_path, f"start lawd_cd={lawd_cd} deal_ym={args.deal_ym}")
        if collector is not None:
            trades = collector.fetch_month(lawd_cd, args.deal_ym)
            inserted = insert_trades(conn, trades)
            _log(log_path, f"collected lawd_cd={lawd_cd} fetched={len(trades)} inserted={inserted}")

        report = analyze_month(conn, lawd_cd, args.deal_ym)
        persist_monthly_stats(conn, report)
        featured_image_path = args.featured_image
        if args.generate_image:
            featured_image_path = create_monthly_report_image(report, lawd_cd)
            all_generated.append(featured_image_path)

        monthly = render_monthly_report(report)
        monthly = _maybe_rewrite(monthly, settings, args.use_llm, "monthly_region_report")
        monthly_path = write_report(monthly, args.deal_ym, lawd_cd)
        _audit_or_raise(monthly_path, args.skip_audit, log_path)
        generated.append(monthly_path)

        rising = render_top_rising_report(report)
        rising = _maybe_rewrite(rising, settings, args.use_llm, "top_rising_report")
        rising_path = write_markdown(
            rising,
            f"{args.deal_ym}_{lawd_cd}_top_rising_report.md",
        )
        _audit_or_raise(rising_path, args.skip_audit, log_path)
        generated.append(rising_path)
        if report.top_volume_complexes:
            item = report.top_volume_complexes[0]
            detail = render_apartment_detail_report(report, item)
            detail = _maybe_rewrite(detail, settings, args.use_llm, "apartment_detail_report")
            detail_path = write_markdown(
                detail,
                f"{args.deal_ym}_{lawd_cd}_{safe_filename(item.apartment_name)}_detail_report.md",
            )
            _audit_or_raise(detail_path, args.skip_audit, log_path)
            generated.append(detail_path)
        if publisher is not None:
            for path in generated:
                result = publisher.publish_markdown_file(
                    path,
                    status=args.status or settings.default_status,
                    categories=args.category,
                    tags=args.tag,
                    featured_image_path=featured_image_path,
                )
                save_wordpress_post(
                    conn,
                    post_type=_post_type_from_path(path),
                    region=report.region_name,
                    deal_ym=args.deal_ym,
                    title=extract_title(path.read_text(encoding="utf-8")),
                    wordpress_post_id=result.post_id,
                    status=result.status,
                )
                _log(log_path, f"published post_id={result.post_id} path={path.name} status={result.status}")
        _log(log_path, f"generated lawd_cd={lawd_cd} files={len(generated)}")
        all_generated.extend(generated)

    for path in all_generated:
        print(path)


def safe_filename(value: str) -> str:
    allowed = []
    for char in value.strip():
        if char.isalnum() or char in ("-", "_"):
            allowed.append(char)
        elif char.isspace():
            allowed.append("_")
    return "".join(allowed) or "apartment"


def _maybe_rewrite(markdown: str, settings: object, enabled: bool, report_type: str) -> str:
    if not enabled:
        return markdown
    return rewrite_markdown_with_llm(
        markdown,
        LlmRewriteConfig(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
        ),
        report_type=report_type,
    )


def _log(path: Path, message: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} {message}\n")


def _audit_or_raise(path: Path, skip: bool, log_path: Path) -> None:
    if skip:
        return
    result = audit_markdown_file(path)
    print(format_audit_result(result))
    _log(log_path, f"audit path={path.name} errors={len(result.errors)} warnings={len(result.warnings)}")
    if not result.passed:
        raise SystemExit(1)


def _post_type_from_path(path: Path) -> str:
    name = path.name
    if "top_rising" in name:
        return "top_rising_report"
    if "detail" in name:
        return "apartment_detail_report"
    return "monthly_region_report"


if __name__ == "__main__":
    main()
