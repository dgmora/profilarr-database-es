-- Spanish Balanced variants are derived from the completed upstream profiles.
-- Every rebuild starts from upstream ops and only then applies this tweak.
-- Foreign keys to quality_profiles(name) use ON UPDATE CASCADE, preserving
-- quality groups, quality ordering, custom format scores, languages, and tags.

UPDATE quality_profiles
SET name = '1080p Balanced - Spanish+Original'
WHERE name = '1080p Balanced';

UPDATE quality_profiles
SET name = '2160p Balanced - Spanish+Original'
WHERE name = '2160p Balanced';

-- Inherited language bans reject valid Spanish-only (dubbed) releases.
-- Remove their scores from these profiles, not their shared CF definitions.
-- This covers sonarr, radarr, and any inherited 'all' score.
DELETE FROM quality_profile_custom_formats
WHERE quality_profile_name IN (
  '1080p Balanced - Spanish+Original',
  '2160p Balanced - Spanish+Original'
)
AND custom_format_name IN ('Not Original', 'Not Original or English');

-- A release without matching positive quality CFs must remain eligible if it
-- includes Spanish. The explicit "Not Spanish" CF in the next tweak rejects
-- missing Spanish instead.
UPDATE quality_profiles
SET minimum_custom_format_score = 0
WHERE name IN (
  '1080p Balanced - Spanish+Original',
  '2160p Balanced - Spanish+Original'
);

-- Radarr's quality-profile language must be Any when language filtering is
-- implemented with CFs. Sonarr uses the same shared profile in Profilarr.
DELETE FROM quality_profile_languages
WHERE quality_profile_name IN (
  '1080p Balanced - Spanish+Original',
  '2160p Balanced - Spanish+Original'
);

INSERT INTO quality_profile_languages (quality_profile_name, language_name, type)
SELECT name, 'Any', 'simple'
FROM quality_profiles
WHERE name IN (
  '1080p Balanced - Spanish+Original',
  '2160p Balanced - Spanish+Original'
);
