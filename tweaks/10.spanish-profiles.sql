-- Convert every completed upstream quality profile into its Spanish variant.
-- Each PCD rebuild starts from upstream ops, so this transformation runs once.
-- Foreign keys use ON UPDATE CASCADE to retain inherited quality settings,
-- groups, ordering, tags, and non-language custom-format scores.

UPDATE quality_profiles
SET name = name || ' - Spanish+Original';

-- Upstream original/English bans can reject Spanish-only releases. Remove the
-- assignments for every Spanish profile, preserving other upstream scores.
DELETE FROM quality_profile_custom_formats
WHERE custom_format_name IN ('Not Original', 'Not Original or English');

-- The Spanish-language rejection CF added by the next tweak provides the
-- explicit language gate instead of the upstream minimum score.
UPDATE quality_profiles SET minimum_custom_format_score = 0;

-- Radarr languages are filtered by custom formats; Sonarr uses the same
-- shared PCD quality profiles but ignores this field.
DELETE FROM quality_profile_languages;

INSERT INTO quality_profile_languages (quality_profile_name, language_name, type)
SELECT name, 'Any', 'simple'
FROM quality_profiles;
