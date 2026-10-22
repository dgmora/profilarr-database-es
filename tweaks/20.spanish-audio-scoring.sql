-- Audio language requirements are independent of the indexer.
-- "Spanish" means the standard Spanish (Castilian) language enum, not
-- the distinct "Spanish (Latino)" enum. Unknown language fails closed.
--
-- Scoring is additive:
--   Original + Spanish + DUAL in title: +3000
--   Original + Spanish:                 +2000
--   Spanish without identified Original:   0
--   No identified Spanish:           -100000000
-- The DUAL marker is only a naming heuristic, not proof of exactly two tracks.
-- Small positive scores preserve Dictionarry's upstream quality ranking and
-- upgrade thresholds. The large negative score beats upstream quality bonuses.

INSERT INTO custom_formats (name, description) VALUES
  ('ES: Not Spanish', 'Reject releases where Spanish audio is not identified.'),
  ('ES: Original + Spanish', 'Prefer releases with both original-language and Spanish audio.'),
  ('ES: Original + Spanish DUAL', 'Additional preference for Original + Spanish releases explicitly marked DUAL.');

INSERT INTO tags (name) VALUES ('Language') ON CONFLICT(name) DO NOTHING;

INSERT INTO custom_format_tags (custom_format_name, tag_name) VALUES
  ('ES: Not Spanish', 'Language'),
  ('ES: Original + Spanish', 'Language'),
  ('ES: Original + Spanish DUAL', 'Language');

-- Condition negate=1 reverses "contains Spanish" for the rejection CF.
INSERT INTO custom_format_conditions
  (custom_format_name, name, type, arr_type, negate, required) VALUES
  ('ES: Not Spanish', 'Spanish', 'language', 'all', 1, 1),
  ('ES: Original + Spanish', 'Original', 'language', 'all', 0, 1),
  ('ES: Original + Spanish', 'Spanish', 'language', 'all', 0, 1),
  ('ES: Original + Spanish DUAL', 'Original', 'language', 'all', 0, 1),
  ('ES: Original + Spanish DUAL', 'Spanish', 'language', 'all', 0, 1),
  ('ES: Original + Spanish DUAL', 'DUAL marker', 'release_title', 'all', 0, 1);

INSERT INTO condition_languages
  (custom_format_name, condition_name, language_name, except_language) VALUES
  ('ES: Not Spanish', 'Spanish', 'Spanish', 0),
  ('ES: Original + Spanish', 'Original', 'Original', 0),
  ('ES: Original + Spanish', 'Spanish', 'Spanish', 0),
  ('ES: Original + Spanish DUAL', 'Original', 'Original', 0),
  ('ES: Original + Spanish DUAL', 'Spanish', 'Spanish', 0);

INSERT INTO regular_expressions (name, pattern, description)
VALUES ('ES: DUAL marker', '(?i)(?:^|[ ._-])DUAL(?:$|[ ._-])', 'An explicit DUAL word in a release title (not a track-count guarantee).');

INSERT INTO condition_patterns (custom_format_name, condition_name, regular_expression_name)
VALUES ('ES: Original + Spanish DUAL', 'DUAL marker', 'ES: DUAL marker');

-- Shared 'all' scores apply to both Sonarr and Radarr.
INSERT INTO quality_profile_custom_formats
  (quality_profile_name, custom_format_name, arr_type, score)
SELECT qp.name, cf.name, 'all', cf.score
FROM quality_profiles qp
CROSS JOIN (
  SELECT 'ES: Not Spanish' AS name, -100000000 AS score
  UNION ALL SELECT 'ES: Original + Spanish', 2000
  UNION ALL SELECT 'ES: Original + Spanish DUAL', 1000
) AS cf
WHERE qp.name IN (
  '1080p Balanced - Spanish+Original',
  '2160p Balanced - Spanish+Original'
);
