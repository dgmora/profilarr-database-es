#!/usr/bin/env python3
"""Rebuild the PCD from upstream operations + tweaks and assert inheritance.

PCD_SCHEMA_DIR must point at the ops/ directory of the schema version
declared in pcd.json. Only Python's sqlite3 standard library is required.
"""

import os
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_TO_SPANISH = {
    "1080p Balanced": "1080p Balanced - Spanish+Original",
    "2160p Balanced": "2160p Balanced - Spanish+Original",
}
LANGUAGE_BANS = {"Not Original", "Not Original or English"}
EXPECTED_SCORES = {
    "ES: Not Spanish": -100_000_000,
    "ES: Original + Spanish": 2_000,
    "ES: Original + Spanish DUAL": 1_000,
}


def ordered_ops(path: Path):
    assert path.is_dir(), f"Missing SQL operations directory: {path}"
    files = list(path.glob("*.sql"))
    assert files, f"No SQL operations in {path}"
    return sorted(
        files,
        key=lambda p: (
            int(p.name.split(".", 1)[0]) if p.name.split(".", 1)[0].isdigit() else 10**9,
            p.name,
        ),
    )


def apply(conn: sqlite3.Connection, path: Path):
    for sql_file in ordered_ops(path):
        try:
            conn.executescript(sql_file.read_text(encoding="utf-8"))
        except sqlite3.Error as exc:
            raise AssertionError(f"SQLite compile failed at {sql_file}: {exc}") from exc


def rows(conn: sqlite3.Connection, table: str, profile_name: str):
    return sorted(
        tuple(row)
        for row in conn.execute(
            f"SELECT * FROM {table} WHERE quality_profile_name = ?",
            (profile_name,),
        )
    )


def compare_inherited(conn, before):
    for source, target in SOURCE_TO_SPANISH.items():
        assert conn.execute(
            "SELECT 1 FROM quality_profiles WHERE name = ?", (source,)
        ).fetchone() is None, f"Unrenamed profile: {source}"

        actual = conn.execute(
            """SELECT id, description, upgrades_allowed,
                      upgrade_until_score, upgrade_score_increment
               FROM quality_profiles WHERE name = ?""",
            (target,),
        ).fetchone()
        assert actual == before[source]["general"], f"Profile settings drifted: {target}"

        for table in ("quality_groups", "quality_group_members",
                      "quality_profile_qualities", "quality_profile_tags"):
            current = rows(conn, table, target)
            # Every row references the profile by name. All other fields
            # (including groups, order, enabled flags and row IDs) must match.
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
            idx = cols.index("quality_profile_name")
            normalized = sorted(
                tuple(source if i == idx else value for i, value in enumerate(row))
                for row in current
            )
            assert normalized == before[source][table], (
                f"Upstream {table} was not inherited by {target}"
            )

        # Existing upstream scores survive except its original/English bans.
        old_scores = {
            (cf, arr): score for cf, arr, score in before[source]["scores"]
            if cf not in LANGUAGE_BANS
        }
        new_scores = {
            (cf, arr): score for cf, arr, score in conn.execute(
                """SELECT custom_format_name, arr_type, score
                   FROM quality_profile_custom_formats WHERE quality_profile_name = ?""",
                (target,),
            )
            if cf not in EXPECTED_SCORES
        }
        assert old_scores == new_scores, f"Upstream CF scores drifted: {target}"

        language = list(conn.execute(
            """SELECT language_name, type FROM quality_profile_languages
               WHERE quality_profile_name = ?""", (target,)
        ))
        assert language == [("Any", "simple")], f"Expected Any: {target}"

        minimum = conn.execute(
            "SELECT minimum_custom_format_score FROM quality_profiles WHERE name = ?",
            (target,),
        ).fetchone()[0]
        assert minimum == 0, f"Incorrect minimum score: {target}"

        scores = dict(conn.execute(
            """SELECT custom_format_name, score FROM quality_profile_custom_formats
               WHERE quality_profile_name = ? AND arr_type = 'all'
                 AND custom_format_name LIKE 'ES: %'""",
            (target,),
        ))
        assert scores == EXPECTED_SCORES, f"Incorrect Spanish scoring: {target}"
        assert not conn.execute(
            """SELECT 1 FROM quality_profile_custom_formats
               WHERE quality_profile_name = ?
                 AND custom_format_name IN ('Not Original', 'Not Original or English')""",
            (target,),
        ).fetchone(), f"Inherited language ban remains: {target}"


def test_conditions(conn):
    expected = {
        "ES: Not Spanish": [
            ("Spanish", "language", "all", 1, 1, "Spanish"),
        ],
        "ES: Original + Spanish": [
            ("Original", "language", "all", 0, 1, "Original"),
            ("Spanish", "language", "all", 0, 1, "Spanish"),
        ],
        "ES: Original + Spanish DUAL": [
            ("Original", "language", "all", 0, 1, "Original"),
            ("Spanish", "language", "all", 0, 1, "Spanish"),
            ("DUAL marker", "release_title", "all", 0, 1, None),
        ],
    }
    for cf, conditions in expected.items():
        actual = list(conn.execute(
            """SELECT c.name, c.type, c.arr_type, c.negate, c.required,
                      l.language_name
               FROM custom_format_conditions c
               LEFT JOIN condition_languages l
                 ON l.custom_format_name = c.custom_format_name
                AND l.condition_name = c.name
               WHERE c.custom_format_name = ? ORDER BY c.name""",
            (cf,),
        ))
        assert sorted(actual) == sorted(conditions), (
            f"Wrong conditions for {cf}: {actual}"
        )

    regex = conn.execute(
        """SELECT r.pattern
           FROM condition_patterns p
           JOIN regular_expressions r ON r.name = p.regular_expression_name
           WHERE p.custom_format_name = 'ES: Original + Spanish DUAL'
             AND p.condition_name = 'DUAL marker'"""
    ).fetchone()
    assert regex, "DUAL marker regex is missing"
    assert re.search(regex[0], "Slow.Horses.S01E01.DUAL.1080p")
    assert not re.search(regex[0], "Slow.Horses.S01E01.MULTI.1080p")
    assert not re.search(regex[0], "Slow.Horses.S01E01.INDUAL.1080p")


def main():
    schema_ops = os.environ.get("PCD_SCHEMA_DIR")
    assert schema_ops, "Set PCD_SCHEMA_DIR to the versioned schema's ops/ directory"
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1

    apply(conn, Path(schema_ops))
    apply(conn, ROOT / "ops")
    before = {}
    for source in SOURCE_TO_SPANISH:
        general = conn.execute(
            """SELECT id, description, upgrades_allowed,
                      upgrade_until_score, upgrade_score_increment
               FROM quality_profiles WHERE name = ?""",
            (source,),
        ).fetchone()
        assert general, f"Upstream removed/renamed source profile: {source}"
        before[source] = {
            "general": general,
            "scores": list(conn.execute(
                """SELECT custom_format_name, arr_type, score
                   FROM quality_profile_custom_formats WHERE quality_profile_name = ?""",
                (source,),
            )),
        }
        for table in ("quality_groups", "quality_group_members",
                      "quality_profile_qualities", "quality_profile_tags"):
            before[source][table] = rows(conn, table, source)

    count_before = conn.execute("SELECT COUNT(*) FROM quality_profiles").fetchone()[0]
    apply(conn, ROOT / "tweaks")
    assert conn.execute("SELECT COUNT(*) FROM quality_profiles").fetchone()[0] == count_before
    compare_inherited(conn, before)
    test_conditions(conn)
    violations = list(conn.execute("PRAGMA foreign_key_check"))
    assert not violations, f"Foreign-key violations: {violations[:10]}"
    print("PCD compilation, Spanish variants, scores and cascade checks passed.")


if __name__ == "__main__":
    main()
