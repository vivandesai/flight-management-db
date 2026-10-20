import hashlib
import json
from pathlib import Path

from airline.catalogue import REPORTS, TRANSACTIONS, TRIGGERS, ROOT


def test_complete_original_catalogue():
    assert len(REPORTS) == 54
    assert len(TRANSACTIONS) == 10
    assert len(TRIGGERS) == 12
    assert {r.id for r in REPORTS.values()} == ({f"J{i}" for i in range(1, 9)} | {f"G{i}" for i in range(1, 8)} | {f"U{i}" for i in range(1, 15)} | {f"A{i}" for i in range(1, 26)})
    for report in REPORTS.values():
        source = (ROOT / report.source).read_text(encoding="utf-8")
        assert report.sql in source
        assert source.splitlines()[report.line - 1].startswith("SELECT")


def test_original_sql_content_hashes():
    # Normalize checkout line endings only, so Windows and Linux use the same manifest.
    expected = json.loads((Path(__file__).parent / "sql-hashes.json").read_text())
    additions = {"sql/dba/01_entity_operations.sql", "sql/views/01_management_views.sql"}
    assert set(expected) | additions == {p.relative_to(ROOT).as_posix() for p in (ROOT / "sql").rglob("*.sql")}
    for path, digest in expected.items():
        assert hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest() == digest, path
