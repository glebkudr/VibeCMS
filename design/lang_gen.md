# Multilingual Content Generation Design (LLM Translation Pipeline)

## Problem Statement

To support a multilingual static site, we need an automated pipeline that generates high-quality translations of articles into multiple target languages using an LLM API. The system must store and manage translations, generate language-specific slugs, and ensure SEO best practices (hreflang, translated slugs, etc.) are followed during static site generation.

## Requirements

- Integrate with an LLM API (to be specified) for automated translation of article content, titles, and slugs.
- Store translations in MongoDB under the `translations` field for each article, e.g.:
  ```json
  {
    "slug": "kak-gotovit-plov",
    "translations": {
      "ru": { "title": "Как готовить плов", "slug": "kak-gotovit-plov", "content_md": "..." },
      "en": { "title": "How to cook plov", "slug": "how-to-cook-plov", "content_md": "..." },
      ...
    },
    ...
  }
  ```
- For each article, generate missing translations for all supported languages.
- Generate language-specific slugs (SEO-friendly, translated, URL-safe).
- Support batch and incremental translation (only missing or updated fields).
- Allow manual editing/override of translations in the admin panel (future scope).
- Ensure all translations are available before static generation.
- Log all translation actions and errors.

## Architecture Overview

- **Translation Service**: Python module/class that calls the LLM API for translation.
- **Integration Point**: Can be run as a separate script or as part of the static generation pipeline (pre-generation step).
- **MongoDB**: Stores all translations under each article document.
- **Slug Generation**: Use LLM or a slugify library to generate translated, URL-safe slugs for each language.
- **Logging**: Log translation requests, responses, and errors.

## Implementation Plan

1. **Translation Service**
    - Implement a Python class/module to interact with the LLM API.
    - Methods: `translate_text(text, source_lang, target_lang)`, `generate_slug(text, lang)`.
    - Support API key/configuration via environment variables.

2. **Translation Pipeline**
    - For each article, for each supported language:
        - If translation is missing or outdated, call the translation service for `title`, `content_md`, and `slug`.
        - Store results in `translations[lang]` in MongoDB.
    - Optionally, mark translations as machine-generated for later review.

3. **Slug Generation**
    - Translate the original slug or title to the target language.
    - Slugify the result (URL-safe, lowercase, hyphens).
    - Ensure uniqueness per language.

4. **Integration with Static Generator**
    - Run translation pipeline before static generation.
    - Ensure all required translations exist for all published articles.
    - If translation is missing, log and skip or raise error (configurable).

5. **SEO and hreflang**
    - Ensure each generated HTML page includes hreflang tags for all available languages.
    - Use translated slugs in URLs.
    - Optionally, generate language-specific sitemaps.

6. **Testing**
    - Test translation quality and slug correctness.
    - Test static generation with multilingual content.
    - Verify hreflang and SEO compliance.

## Integration Points
- Can be run as a standalone script (`python generator/translate.py`) or as a pre-step in the main generator.
- Should be idempotent: re-running should not overwrite manual edits.
- Should support dry-run and verbose logging modes.

## References
- [hreflang SEO best practices](https://ahrefs.com/blog/hreflang/)
- [Google multilingual SEO guide](https://developers.google.com/search/docs/specialty/international/localized-versions)

---

*This document describes the design and implementation plan for the multilingual content generation pipeline using an LLM API. All implementation should follow this design for consistency, SEO, and maintainability.* 