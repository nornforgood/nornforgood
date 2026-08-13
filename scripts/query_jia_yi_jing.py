from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "jia_yi_jing_acupuncture.db"


def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"資料庫不存在: {DB_PATH}\n請先執行: py -3 scripts/build_jia_yi_jing_db.py"
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def search_disease(keyword: str | None = None) -> list[sqlite3.Row]:
    sql = """
        SELECT d.id, d.name, d.category, d.description
        FROM diseases d
        WHERE (? IS NULL OR d.name LIKE '%' || ? || '%' OR d.category LIKE '%' || ? || '%')
        ORDER BY d.id
    """
    with connect() as conn:
        return conn.execute(sql, (keyword, keyword, keyword)).fetchall()


def search_point(keyword: str | None = None) -> list[sqlite3.Row]:
    sql = """
        SELECT a.id, a.name, a.pinyin, m.name AS meridian_name, a.location, a.note, a.classic_code
        FROM acupoints a
        JOIN meridians m ON m.id = a.meridian_id
        WHERE (? IS NULL OR a.name LIKE '%' || ? || '%' OR a.pinyin LIKE '%' || ? || '%' OR m.name LIKE '%' || ? || '%')
        ORDER BY a.id
    """
    with connect() as conn:
        return conn.execute(sql, (keyword, keyword, keyword, keyword)).fetchall()


def search_meridian(keyword: str | None = None) -> list[sqlite3.Row]:
    sql = """
        SELECT m.id, m.name, m.code, m.category, m.description
        FROM meridians m
        WHERE (? IS NULL OR m.name LIKE '%' || ? || '%' OR m.code LIKE '%' || ? || '%' OR m.category LIKE '%' || ? || '%')
        ORDER BY m.id
    """
    with connect() as conn:
        return conn.execute(sql, (keyword, keyword, keyword, keyword)).fetchall()


def query_points_by_disease(disease_name: str) -> list[sqlite3.Row]:
    sql = """
        SELECT a.name AS point_name, a.pinyin, m.name AS meridian_name, d.name AS disease_name, p.evidence
        FROM point_disease p
        JOIN acupoints a ON a.id = p.point_id
        JOIN meridians m ON m.id = a.meridian_id
        JOIN diseases d ON d.id = p.disease_id
        WHERE d.name LIKE '%' || ? || '%'
        ORDER BY a.id
    """
    with connect() as conn:
        return conn.execute(sql, (disease_name,)).fetchall()


def query_points_by_meridian(meridian_name: str) -> list[sqlite3.Row]:
    sql = """
        SELECT a.name AS point_name, a.pinyin, m.name AS meridian_name, a.location
        FROM acupoints a
        JOIN meridians m ON m.id = a.meridian_id
        WHERE m.name LIKE '%' || ? || '%'
        ORDER BY a.id
    """
    with connect() as conn:
        return conn.execute(sql, (meridian_name,)).fetchall()


def print_rows(rows: list[sqlite3.Row], headers: list[str]) -> None:
    if not rows:
        print("查無資料")
        return
    widths = [len(h) for h in headers]
    for row in rows:
        values = [str(row[h]) for h in headers]
        for i, value in enumerate(values):
            widths[i] = max(widths[i], len(value))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        values = [str(row[h]) for h in headers]
        print(fmt.format(*values))


def main() -> None:
    parser = argparse.ArgumentParser(description="甲乙經穴位、經絡、病症查詢工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    disease_parser = subparsers.add_parser("disease", help="按病症查詢")
    disease_parser.add_argument("keyword", nargs="?", default=None)

    point_parser = subparsers.add_parser("point", help="按穴位查詢")
    point_parser.add_argument("keyword", nargs="?", default=None)

    meridian_parser = subparsers.add_parser("meridian", help="按經絡查詢")
    meridian_parser.add_argument("keyword", nargs="?", default=None)

    by_disease_parser = subparsers.add_parser("by-disease", help="查某病症對應穴位")
    by_disease_parser.add_argument("keyword")

    by_meridian_parser = subparsers.add_parser("by-meridian", help="查某經絡對應穴位")
    by_meridian_parser.add_argument("keyword")

    args = parser.parse_args()

    try:
        if args.command == "disease":
            rows = search_disease(args.keyword)
            print_rows(rows, ["id", "name", "category", "description"])
        elif args.command == "point":
            rows = search_point(args.keyword)
            print_rows(rows, ["id", "name", "pinyin", "meridian_name", "location", "classic_code"])
        elif args.command == "meridian":
            rows = search_meridian(args.keyword)
            print_rows(rows, ["id", "name", "code", "category", "description"])
        elif args.command == "by-disease":
            rows = query_points_by_disease(args.keyword)
            print_rows(rows, ["point_name", "pinyin", "meridian_name", "disease_name", "evidence"])
        elif args.command == "by-meridian":
            rows = query_points_by_meridian(args.keyword)
            print_rows(rows, ["point_name", "pinyin", "meridian_name", "location"])
    except FileNotFoundError as exc:
        print(exc)


if __name__ == "__main__":
    main()
