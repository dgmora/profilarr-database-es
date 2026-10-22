# Spanish+Original Dictionarry profiles

This fork keeps Dictionarry's `v2` operations untouched and applies
Git-tracked Spanish customizations under `tweaks/` after upstream SQL:
`schema → ops → tweaks → local user ops`.

## Intended use: one Profilarr, two databases

| Profilarr linked database | Repository | Sync selection |
| --- | --- | --- |
| Dictionarry | `Dictionarry-Hub/database` (`v2`) | Regular upstream profiles |
| Dictionarry Spanish | `dgmora/profilarr-database-es` (`v2`) | Only `1080p Balanced - Spanish+Original` and `2160p Balanced - Spanish+Original` |

Use **different database instance names** in Profilarr. Link the two
repositories in the same Profilarr installation and sync only their intended
profiles into Sonarr/Radarr instances. No second Profilarr service is needed.
`pcd.json` can retain its upstream identity.

## Desired audio priorities

For content whose **original language is not Spanish**, Spanish (Castilian)
audio is required:

1. **Best:** Spanish + original, and no other audio languages.
2. **Next:** Spanish + original + one or more additional audio languages.
3. **Fallback:** Spanish only, or Spanish plus other *non-original* languages.
4. **Reject:** No Spanish audio.

For originally Spanish content, Spanish-only should still be eligible. These
preferences are **within comparable quality tiers**, since Sonarr/Radarr
compare qualities before Custom Format scores. They do not change search
queries (including Spanish/English alternate series titles).

## Implementation

- `tweaks/10.spanish-balanced-profiles.sql` renames the completed
  `1080p Balanced` and `2160p Balanced` profiles; schema foreign keys
  with `ON UPDATE CASCADE` preserve inherited qualities, group ordering,
  tags, and other Custom Format scores. It sets language to `Any` and
  minimum Custom Format score to 0.
- Remove scoring assignments of upstream `Not Original` and
  `Not Original or English` only from the two Spanish variants. Those
  existing rejections would incorrectly ban Spanish-only releases.
- `tweaks/20.spanish-audio-scoring.sql` adds Spanish-prefixed CFs for
  Sonarr and Radarr (`arr_type = 'all'`), following TRaSH's pattern of
  checking **Original + target language** rather than English or title
  markers alone.

| When Spanish is identified | Spanish-language CF score |
| --- | ---: |
| Original + Spanish, DUAL or an explicitly named two-language pair, no advertised third language | +3000 |
| Original + Spanish, number of languages uncertain | +2000 |
| Original + Spanish, explicit list including a third language | +1500 |
| Spanish without identified Original | 0 |
| Spanish not identified | -100000000; below minimum, reject |

Scoring is additive: `Original + Spanish` (+2000), `Likely two languages`
(+1000), `Explicit 3+ languages` (-500), and `Not Spanish` (-100000000).
The 3+-language evidence **suppresses** the likely-two bonus even if `DUAL`
is also present. A bare `MULTi` is *not* evidence of three languages:
it can mean two or more.

### Limits / conscious approximations

- Sonarr/Radarr language conditions test *membership*, not an exact audio
  track count. A DUAL marker or an explicit Spanish/original pair is a
  **heuristic** for two tracks; an unadvertised third track may exist.
- Explicit 3+-language matching covers contiguous language-label lists
  (for example `ENG.ESP.FRA`), not every possible group or tracker
  convention; three tracks may be present without being advertised.
  Conversely, some tokens may describe subtitles rather than audio.
- Parsed release languages depend on titles, indexer-provided metadata,
  and per-indexer settings. Spanish-language indexers often use translated
  series names or omit explicit audio-language tags: without identifiable
  Spanish audio, the profile rejects the release even if it really is dubbed.
  An indexer-specific `MULTi` assumption may help **if validated for that
  indexer**, but the SQL doesn't add such an assumption automatically.
- The `Original` language condition resolves from the media's original
  language where supported. On originally Spanish titles it can match
  Spanish-only audio, so the `Original + Spanish` bonus does *not*
  guarantee two distinct tracks.
- `Spanish` uses the standard Castilian language enum; `Spanish (Latino)`
  is a separate value. Naming and parsing can still be ambiguous.
- Retained Dictionarry quality groups, scores, and upgrade thresholds
  continue to affect ranking. A preferred language combination cannot
  guarantee victory over a different, higher-ranked quality tier.
- This SQL affects scoring/selection, **not Sonarr's search terms**
  (for example translated series titles versus their original titles).

Relevant TRaSH precedents:
[German DL](https://github.com/TRaSH-Guides/Guides/blob/master/docs/json/sonarr/cf/german-dl.json),
[Original + French](https://github.com/TRaSH-Guides/Guides/blob/master/docs/json/sonarr/cf/language-original-plus-french.json),
and [MULTi](https://github.com/TRaSH-Guides/Guides/blob/master/docs/json/sonarr/cf/multi.json).

## Updating from Dictionarry

Merge/rebase `Dictionarry-Hub/database` `v2` into this fork's `v2`;
the fork's customizations live only in `tweaks/` and fork-local
documentation/checks, so upstream `ops/` updates normally merge without
conflict. Profilarr compiles the latest upstream profiles *before*
applying the language tweaks. A renamed/removed upstream source profile
should fail validation rather than silently produce a broken variant.

CI replays the schema, upstream SQL, and tweaks in SQLite, verifies inherited
relations and FK integrity, and **simulates CF conditions** on an illustrative
release-name matrix. These tests do **not** call Sonarr/Radarr parsers or
prove track counts. Follow-up validation should inspect actual releases
from DonTorrent/EliteTorrent in Sonarr/Radarr Interactive Search.

Run locally with the matching schema dependency:

```sh
git clone --depth 1 --branch 1.1.0 https://github.com/Dictionarry-Hub/schema.git /tmp/dictionarry-pcd-schema
PCD_SCHEMA_DIR=/tmp/dictionarry-pcd-schema/ops python3 tests/validate_database.py
```
