# Spanish+Original Dictionarry profiles

This fork keeps Dictionarry's `v2` operations unchanged and applies all
Spanish customization in `tweaks/` **after** upstream SQL has been replayed.
Profilarr uses the order `schema → ops → tweaks → local user ops`.

## Linked databases (one Profilarr instance)

Link both repositories independently and give them different **instance names**:

| Profilarr database instance | Repository | Profiles to sync |
| --- | --- | --- |
| Dictionarry | `Dictionarry-Hub/database` (branch `v2`) | Regular Dictionarry profiles |
| Dictionarry Spanish | `dgmora/profilarr-database-es` (branch `v2`) | `1080p Balanced - Spanish+Original`, `2160p Balanced - Spanish+Original` |

The instance name is user-configurable; `pcd.json` can stay identical to
upstream. Only sync the selected Spanish variants from the fork. Profiles from
other upstream definitions are still present in its compiled database, but
aren't intended to be synced from that source.

The Spanish variants can be synced into Sonarr ES and/or Radarr ES. Regular
series and movies keep using the ordinary profiles; there is no need for a
second Profilarr process or persistent Profilarr UI edits. Linking databases
and selecting sync profiles are one-time Profilarr setup operations, not
declarative repository changes.

## What the tweaks change

- `tweaks/10.spanish-balanced-profiles.sql` renames the completed upstream
  `1080p Balanced` and `2160p Balanced` entities. Their associated qualities,
  groups, tags, and CF scores follow through schema `ON UPDATE CASCADE`.
  Sets preferred language to `Any` (required for Radarr CF language filtering)
  and minimum CF score to 0. Removes **scoring assignments**, only for these
  variants, of the upstream `Not Original` and `Not Original or English`
  rejection CFs so Spanish-only releases are allowed.
- `tweaks/20.spanish-audio-scoring.sql` adds three Spanish-scoped CFs and
  assigns them only to the Spanish variants, for Sonarr and Radarr.

| Detected languages/title | Language CF contribution |
| --- | ---: |
| Original + Spanish with explicit DUAL marker | +3000 |
| Original + Spanish without DUAL marker | +2000 |
| Spanish alone, or Spanish with other non-original languages | 0 |
| Spanish not identified | -100000000 (reject at min score 0) |

The two positive bonuses are additive (+2000 and +1000). They are intentionally
small relative to Dictionarry's quality CFs, so quality tiers and
`upgrade_until_score` retain their general behavior. Thus these are
preferences *within* upstream quality scoring, not a guarantee that any
dual-audio release outranks every higher-quality Spanish-only release.

`Spanish` means the parser's standard Spanish language; `Spanish (Latino)`
is a distinct value and **does not count**. This is aimed at Castilian-dubbed
releases from DonTorrent, EliteTorrent, and other indexers.

**Limitations:**

- A DUAL marker isn't proof of exactly two audio tracks; a release with three
  languages and DUAL in its name may receive the highest bonus, while a
  real two-track release without the word DUAL gets the second tier.
- Language conditions depend on Sonarr/Radarr's release-name parsing and
  indexer metadata. Releases without an *identified* Spanish audio track are
  rejected even when the file might contain one. A subtitle-only VOSE release
  must not count as Spanish audio.
- Original-language detection depends on the series/movie metadata. For
  originally Spanish-language titles, "Original + Spanish" may not mean two
  distinct tracks; the preferences are primarily designed for non-Spanish
  originals.
- These CFs affect **ranking/filtering only**, not Sonarr's English-title
  searches (for example `Slow Horses` vs `Caballos Lentos`).
- Dictionarry's separate banned-release-group / quality rules remain intact.

## Updating from upstream

Track `Dictionarry-Hub/database` as an upstream Git remote and merge/rebase
its `v2` branch into this fork's `v2`. Only the `tweaks/` files and these
fork-local checks/docs diverge, so upstream `ops/` changes normally merge
without conflict. The next PCD compile rebuilds the **latest upstream**
profiles before applying these Spanish tweaks.

The GitHub workflow replays the schema, all upstream operations, and our tweaks
in SQLite, checking that the profile inheritance and language CFs still work.
If upstream renames/removes a source profile or changes its schema incompatibly,
the check fails rather than silently losing Spanish variants.

Run the same check locally (with a compatible version of the schema checkout):

```sh
git clone --depth 1 --branch 1.1.0 https://github.com/Dictionarry-Hub/schema.git /tmp/dictionarry-pcd-schema
PCD_SCHEMA_DIR=/tmp/dictionarry-pcd-schema/ops python3 tests/validate_database.py
```

For later profile types, add new profile rename mappings in tweak 10 and
include their new names in tweak 20's scoring assignment. Validate the
parent profile's existing language bans before extending.
