# Dictionarry Database — Spanish Profiles

An **unofficial fork** of the [Dictionarry database](https://github.com/Dictionarry-Hub/database) for [Profilarr](https://github.com/Dictionarry-Hub/profilarr). It adds Spanish (Castilian) audio preferences to Dictionarry's Balanced quality profiles while retaining upstream quality settings and updates.

## Profiles

- `1080p Balanced - Spanish+Original`
- `2160p Balanced - Spanish+Original`

Both require **Spanish audio** and, for non-Spanish originals, prefer releases in this order:

1. **Original + Spanish only** (two audio languages).
2. **Original + Spanish + other languages** (three or more).
3. **Spanish only**, or Spanish with other languages but not the original.
4. **No Spanish:** reject.

Release names and indexer metadata cannot always prove the number of audio tracks. The profiles use language detection plus naming hints to approximate the two-versus-three preference; `MULTi` alone does not imply three or more languages. Preferences are scored within comparable quality tiers.

## Using the database

Keep **one Profilarr instance** and link **two databases**:

- [Official Dictionarry](https://github.com/Dictionarry-Hub/database) for your regular profiles.
- This fork for the two Spanish profiles above.

Selectively sync the Spanish profiles to your Sonarr/Radarr instance(s). The fork inherits upstream profile definitions from `ops/` and applies its changes in `tweaks/`, so updates from Dictionarry can be merged without maintaining copied profiles by hand.

See [SPANISH.md](SPANISH.md) for implementation details, limitations and maintenance instructions.

## Credits

Based on the [Dictionarry database](https://github.com/Dictionarry-Hub/database). For upstream profiles and general Profilarr support, see the [Dictionarry documentation](https://dictionarry.dev) and [Dictionarry Discord](https://discord.com/invite/Y9TYP6jeYZ).
