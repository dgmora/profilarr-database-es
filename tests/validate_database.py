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
    "ES: Likely two languages": 1_000,
    "ES: Explicit 3+ languages": -500,
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
            ("Spanish", "language", "all", 1, 1, "Spanish", None),
        ],
        "ES: Original + Spanish": [
            ("Original", "language", "all", 0, 1, "Original", None),
            ("Spanish", "language", "all", 0, 1, "Spanish", None),
        ],
        "ES: Likely two languages": [
            ("Original", "language", "all", 0, 1, "Original", None),
            ("Spanish", "language", "all", 0, 1, "Spanish", None),
            ("DUAL or named pair", "release_title", "all", 0, 1, None, "ES: DUAL or named pair"),
            ("No three-language list", "release_title", "all", 1, 1, None, "ES: Three-language list"),
        ],
        "ES: Explicit 3+ languages": [
            ("Original", "language", "all", 0, 1, "Original", None),
            ("Spanish", "language", "all", 0, 1, "Spanish", None),
            ("Three-language list", "release_title", "all", 0, 1, None, "ES: Three-language list"),
        ],
    }

    for cf, conditions in expected.items():
        actual = list(conn.execute(
            """SELECT c.name, c.type, c.arr_type, c.negate, c.required,
                      l.language_name, p.regular_expression_name
               FROM custom_format_conditions c
               LEFT JOIN condition_languages l
                 ON l.custom_format_name = c.custom_format_name
                AND l.condition_name = c.name
               LEFT JOIN condition_patterns p
                 ON p.custom_format_name = c.custom_format_name
                AND p.condition_name = c.name
               WHERE c.custom_format_name = ? ORDER BY c.name""",
            (cf,),
        ))
        assert sorted(actual) == sorted(conditions), (
            f"Wrong conditions for {cf}: {actual}"
        )


def simulated_language_score(conn, profile, title, languages, original):
    """Validate the PCD conditions on example inputs, NOT Sonarr's release parser.

    The caller supplies the languages Sonarr is assumed to have parsed.
    Sonarr and Radarr should be independently checked with actual search results.
    """
    sql = """SELECT p.custom_format_name, p.score, c.name, c.type, c.negate,
                    c.required, l.language_name, r.pattern
             FROM quality_profile_custom_formats p
             JOIN custom_format_conditions c
               ON c.custom_format_name = p.custom_format_name
             LEFT JOIN condition_languages l
               ON l.custom_format_name = c.custom_format_name
              AND l.condition_name = c.name
             LEFT JOIN condition_patterns cp
               ON cp.custom_format_name = c.custom_format_name
              AND cp.condition_name = c.name
             LEFT JOIN regular_expressions r
               ON r.name = cp.regular_expression_name
             WHERE p.quality_profile_name = ? AND p.arr_type = 'all'
               AND p.custom_format_name LIKE 'ES: %'
             ORDER BY p.custom_format_name, c.name"""
    grouped = {}
    for cf, score, name, kind, negate, required, language, regex in conn.execute(
        sql, (profile,)
    ):
        if kind == "language":
            expected = original if language == "Original" else language
            matches = expected in languages
        elif kind == "release_title":
            assert regex, (cf, name)
            matches = bool(re.search(regex, title))
        else:
            raise AssertionError(f"Unexpected condition kind: {kind}")
        if negate:
            matches = not matches
        assert required, f"Language CF condition unexpectedly optional: {cf}/{name}"
        if cf not in grouped:
            grouped[cf] = (score, [])
        else:
            assert grouped[cf][0] == score
        grouped[cf][1].append(matches)

    assert set(grouped) == set(EXPECTED_SCORES)
    return sum(score for score, matches in grouped.values() if all(matches))


def test_language_ranking(conn):
    # The first four represent the user's requested priority for an
    # originally English-language series. These are illustrative release
    # titles, not claimed examples observed on DonTorrent/EliteTorrent.
    cases = [
        ("likely dual marker", "Show.S01E01.ESP.ENG.DUAL.1080p",
         {"Spanish", "English"}, "English", 3000),
        ("two named languages", "Show.S01E01.ESP.ENG.1080p",
         {"Spanish", "English"}, "English", 3000),
        ("repeated language after Spanish is not 3+", "Show.S01E01.ESP.ENG.ENG.1080p",
         {"Spanish", "English"}, "English", 3000),
        ("repeated original around Spanish is not 3+", "Show.S01E01.ENG.ESP.ENG.1080p",
         {"Spanish", "English"}, "English", 3000),
        ("named third language", "Show.S01E01.ENG.ESP.FRA.MULTi.1080p",
         {"Spanish", "English", "French"}, "English", 1500),
        ("named third despite DUAL", "Show.S01E01.ESP.ENG.FRA.DUAL.1080p",
         {"Spanish", "English", "French"}, "English", 1500),
        ("three languages in another order", "Show.S01E01.FRA.ITA.ESP.1080p",
         {"Spanish", "English", "Italian", "French"}, "English", 1500),
        ("ambiguous MULTi is not 3+", "Show.S01E01.MULTi.1080p",
         {"Spanish", "English"}, "English", 2000),
        ("explicit pair plus MULTi", "Show.S01E01.ENG.ESP.MULTi.1080p",
         {"Spanish", "English"}, "English", 3000),
        ("spanish only", "Show.S01E01.ESP.1080p",
         {"Spanish"}, "English", 0),
        ("spanish plus non-original", "Show.S01E01.ESP.FRA.1080p",
         {"Spanish", "French"}, "English", 0),
        ("english only", "Show.S01E01.ENG.1080p",
         {"English"}, "English", -100_000_000),
        ("original plus third but no spanish", "Show.S01E01.ENG.FRA.1080p",
         {"English", "French"}, "English", -100_000_000),
        ("unrecognized Spanish is rejected", "Show.S01E01.MULTi.1080p",
         {"Unknown"}, "English", -100_000_000),
        ("latino alone is not castilian", "Show.S01E01.LATINO.1080p",
         {"Spanish (Latino)"}, "English", -100_000_000),
        ("spanish-original show still eligible", "Show.S01E01.ESP.1080p",
         {"Spanish"}, "Spanish", 2000),
    ]
    for profile in SOURCE_TO_SPANISH.values():
        for case, title, languages, original, expected in cases:
            actual = simulated_language_score(
                conn, profile, title, languages, original
            )
            assert actual == expected, (
                f"{profile}: {case}: expected {expected}, got {actual}"
            )

    # Preference within a comparable quality tier, not a claim that
    # Sonarr/Radarr will rank across different quality tiers by CF score.
    samples = {
        name: simulated_language_score(conn, next(iter(SOURCE_TO_SPANISH.values())),
                                       title, langs, "English")
        for name, title, langs in [
            ("two", "Show.S01E01.ESP.ENG.DUAL.1080p", {"Spanish", "English"}),
            ("unknown count", "Show.S01E01.MULTi.1080p", {"Spanish", "English"}),
            ("three+", "Show.S01E01.ESP.ENG.FRA.1080p",
             {"Spanish", "English", "French"}),
            ("spanish only", "Show.S01E01.ESP.1080p", {"Spanish"}),
        ]
    }
    assert (samples["two"] > samples["unknown count"] >
            samples["three+"] > samples["spanish only"]), samples


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
    test_language_ranking(conn)
    violations = list(conn.execute("PRAGMA foreign_key_check"))
    assert not violations, f"Foreign-key violations: {violations[:10]}"
    print("PCD compilation, Spanish variants, and simulated language ranking passed.")


if __name__ == "__main__":
    main()
