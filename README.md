# Dictionarry Database — Spanish Profiles

An **unofficial fork** of the [Dictionarry database](https://github.com/Dictionarry-Hub/database) for [Profilarr](https://github.com/Dictionarry-Hub/profilarr). It provides Spanish (Castilian) audio preferences for **every upstream quality profile**, while retaining Dictionarry's quality settings.

## Profiles

Each upstream profile is available with the suffix `- Spanish+Original`, for example `1080p Balanced - Spanish+Original` and `2160p Remux - Spanish+Original`. New upstream profiles receive the same treatment when the fork is updated.

All Spanish variants require detectable **Spanish audio** and prefer, for non-Spanish originals:

1. Original + Spanish only (likely two languages).
2. Original + Spanish + additional languages.
3. Spanish without the original audio.
4. No Spanish: reject.

Audio-track counts are inferred from release names, not verified before download. Preferences are soft scores alongside upstream quality scoring.

## Using the database

Use **one Profilarr instance** with two linked databases:

- [Official Dictionarry](https://github.com/Dictionarry-Hub/database) for regular profiles.
- This fork for Spanish variants.

Select the desired profiles from each database for your Sonarr/Radarr instances. Upstream changes are incorporated by updating the fork from Dictionarry; no manual edits to the Spanish profiles are needed.

See [SPANISH.md](SPANISH.md) for synchronization priority, limitations, and maintenance.

## Credits

Based on the [Dictionarry database](https://github.com/Dictionarry-Hub/database). For upstream profiles and Profilarr support, see the [Dictionarry documentation](https://dictionarry.dev) and [Dictionarry Discord](https://discord.com/invite/Y9TYP6jeYZ).
