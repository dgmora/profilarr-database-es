-- Spanish audio is required; language combinations are preferences on top of
-- inherited Dictionarry quality scores. Language CFs inspect parsed languages,
-- not the file's actual track inventory.
--
-- Additional language score (for non-Spanish originals):
--   Original + Spanish, likely exactly two: +3000 (base + evidence bonus)
--   Original + Spanish, count unknown:      +2000
--   Original + Spanish, 3+ advertised:      +1500 (base - evidence penalty)
--   Spanish without detected Original:         0
--   No detected Spanish:                -100000000 (below minimum CF score)
--
-- DUAL / a two-language token pair is only a *hint*; an unadvertised third
-- audio track remains possible. MULTi by itself does NOT imply 3+ languages.
-- Explicit 3+ token sequences override the likely-dual hint.

INSERT INTO custom_formats (name, description) VALUES
  ('ES: Not Spanish', 'Reject releases where Spanish audio cannot be identified.'),
  ('ES: Original + Spanish', 'Prefer detected original-language plus Spanish audio.'),
  ('ES: Likely two languages', 'Extra preference for original + Spanish with DUAL or an explicit two-language pair, unless 3+ are advertised.'),
  ('ES: Explicit 3+ languages', 'Reduce preference when the release advertises Spanish and at least two other language tokens.');

INSERT INTO tags (name) VALUES ('Language') ON CONFLICT(name) DO NOTHING;

INSERT INTO custom_format_tags (custom_format_name, tag_name) VALUES
  ('ES: Not Spanish', 'Language'),
  ('ES: Original + Spanish', 'Language'),
  ('ES: Likely two languages', 'Language'),
  ('ES: Explicit 3+ languages', 'Language');

INSERT INTO regular_expressions (name, pattern, description) VALUES
  ('ES: DUAL or named pair', '(?i)(?<![A-Za-z])(?:(?:ESP|SPA|ES|CASTELLANO|ESPA[NÑ]OL|SPANISH)[ ._+/\-]+(?:ENG|ING|EN|ENGLISH|FRA|FRE|FR|FRENCH|ITA|IT|ITALIAN|GER|DEU|DE|GERMAN|JPN|JAP|JA|JAPANESE|KOR|KO|KOREAN|POR|PT|PORTUGUESE|RUS|RU|RUSSIAN|CAT|CA|CATALAN)|(?:ENG|ING|EN|ENGLISH|FRA|FRE|FR|FRENCH|ITA|IT|ITALIAN|GER|DEU|DE|GERMAN|JPN|JAP|JA|JAPANESE|KOR|KO|KOREAN|POR|PT|PORTUGUESE|RUS|RU|RUSSIAN|CAT|CA|CATALAN)[ ._+/\-]+(?:ESP|SPA|ES|CASTELLANO|ESPA[NÑ]OL|SPANISH))(?![A-Za-z])|(?<![A-Za-z])DUAL(?:[ ._\-]?AUDIO)?(?![A-Za-z])', 'DUAL or a contiguous Spanish/non-Spanish language pair. These are hints, not verified track counts.'),
  ('ES: Three-language list', '(?i)(?<![A-Za-z])(?:(?:ESP|SPA|ES|CASTELLANO|ESPA[NÑ]OL|SPANISH)[ ._+/\-]+((?:ENG|ING|EN|ENGLISH|FRA|FRE|FR|FRENCH|ITA|IT|ITALIAN|GER|DEU|DE|GERMAN|JPN|JAP|JA|JAPANESE|KOR|KO|KOREAN|POR|PT|PORTUGUESE|RUS|RU|RUSSIAN|CAT|CA|CATALAN))[ ._+/\-]+(?!\1(?=[ ._+/\-]|$))(?:ENG|ING|EN|ENGLISH|FRA|FRE|FR|FRENCH|ITA|IT|ITALIAN|GER|DEU|DE|GERMAN|JPN|JAP|JA|JAPANESE|KOR|KO|KOREAN|POR|PT|PORTUGUESE|RUS|RU|RUSSIAN|CAT|CA|CATALAN)|((?:ENG|ING|EN|ENGLISH|FRA|FRE|FR|FRENCH|ITA|IT|ITALIAN|GER|DEU|DE|GERMAN|JPN|JAP|JA|JAPANESE|KOR|KO|KOREAN|POR|PT|PORTUGUESE|RUS|RU|RUSSIAN|CAT|CA|CATALAN))[ ._+/\-]+(?:ESP|SPA|ES|CASTELLANO|ESPA[NÑ]OL|SPANISH)[ ._+/\-]+(?!\2(?=[ ._+/\-]|$))(?:ENG|ING|EN|ENGLISH|FRA|FRE|FR|FRENCH|ITA|IT|ITALIAN|GER|DEU|DE|GERMAN|JPN|JAP|JA|JAPANESE|KOR|KO|KOREAN|POR|PT|PORTUGUESE|RUS|RU|RUSSIAN|CAT|CA|CATALAN)|((?:ENG|ING|EN|ENGLISH|FRA|FRE|FR|FRENCH|ITA|IT|ITALIAN|GER|DEU|DE|GERMAN|JPN|JAP|JA|JAPANESE|KOR|KO|KOREAN|POR|PT|PORTUGUESE|RUS|RU|RUSSIAN|CAT|CA|CATALAN))[ ._+/\-]+(?!\3(?=[ ._+/\-]|$))(?:ENG|ING|EN|ENGLISH|FRA|FRE|FR|FRENCH|ITA|IT|ITALIAN|GER|DEU|DE|GERMAN|JPN|JAP|JA|JAPANESE|KOR|KO|KOREAN|POR|PT|PORTUGUESE|RUS|RU|RUSSIAN|CAT|CA|CATALAN)[ ._+/\-]+(?:ESP|SPA|ES|CASTELLANO|ESPA[NÑ]OL|SPANISH))(?![A-Za-z])', 'Three adjoining language labels including Spanish and two different non-Spanish tokens; aliases for the same language may still match; MULTi alone does not match.');

INSERT INTO custom_format_conditions
  (custom_format_name, name, type, arr_type, negate, required) VALUES
  ('ES: Not Spanish', 'Spanish', 'language', 'all', 1, 1),
  ('ES: Original + Spanish', 'Original', 'language', 'all', 0, 1),
  ('ES: Original + Spanish', 'Spanish', 'language', 'all', 0, 1),
  ('ES: Likely two languages', 'Original', 'language', 'all', 0, 1),
  ('ES: Likely two languages', 'Spanish', 'language', 'all', 0, 1),
  ('ES: Likely two languages', 'DUAL or named pair', 'release_title', 'all', 0, 1),
  ('ES: Likely two languages', 'No three-language list', 'release_title', 'all', 1, 1),
  ('ES: Explicit 3+ languages', 'Original', 'language', 'all', 0, 1),
  ('ES: Explicit 3+ languages', 'Spanish', 'language', 'all', 0, 1),
  ('ES: Explicit 3+ languages', 'Three-language list', 'release_title', 'all', 0, 1);

INSERT INTO condition_languages
  (custom_format_name, condition_name, language_name, except_language) VALUES
  ('ES: Not Spanish', 'Spanish', 'Spanish', 0),
  ('ES: Original + Spanish', 'Original', 'Original', 0),
  ('ES: Original + Spanish', 'Spanish', 'Spanish', 0),
  ('ES: Likely two languages', 'Original', 'Original', 0),
  ('ES: Likely two languages', 'Spanish', 'Spanish', 0),
  ('ES: Explicit 3+ languages', 'Original', 'Original', 0),
  ('ES: Explicit 3+ languages', 'Spanish', 'Spanish', 0);

INSERT INTO condition_patterns (custom_format_name, condition_name, regular_expression_name) VALUES
  ('ES: Likely two languages', 'DUAL or named pair', 'ES: DUAL or named pair'),
  ('ES: Likely two languages', 'No three-language list', 'ES: Three-language list'),
  ('ES: Explicit 3+ languages', 'Three-language list', 'ES: Three-language list');

-- Shared 'all' assignments apply to both Sonarr and Radarr.
INSERT INTO quality_profile_custom_formats
  (quality_profile_name, custom_format_name, arr_type, score)
SELECT qp.name, cf.name, 'all', cf.score
FROM quality_profiles qp
CROSS JOIN (
  SELECT 'ES: Not Spanish' AS name, -100000000 AS score
  UNION ALL SELECT 'ES: Original + Spanish', 2000
  UNION ALL SELECT 'ES: Likely two languages', 1000
  UNION ALL SELECT 'ES: Explicit 3+ languages', -500
) AS cf
;
