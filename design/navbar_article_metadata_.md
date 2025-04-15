Technical Specification: Implement a Shared Navigation Bar with Auto-Generated Article Links (Custom Jinja2 Static Generator)

1. Goal
Develop a mechanism within a custom static site generator (written in Python, using Jinja2) that automatically includes a shared navigation bar. This navigation bar will display links to articles grouped by categories so that whenever new articles are added, they appear under their respective categories without any manual edits to the navigation template.

2. Functional Requirements
Global Navigation Bar

Provide a reusable Jinja2 template partial for the navigation bar.

The navigation bar must be included on all relevant pages.

Article Metadata

Each article should include metadata specifying at least title, category, and slug or url.

The generator must parse this metadata from the article’s front matter (e.g., YAML/JSON/TOML within the Markdown files) or from a separate file.

Category–Article Mapping

Automatically build a mapping from categories to their articles.

Each entry must include:

The category name

The article title

The article’s URL/permalink

Automatic Updates

When new articles are added (with valid metadata), they must automatically appear in the navigation bar under the correct category.

No manual modifications to the navigation template are required for new articles.

Multi-Category Support (optional but preferred)

An article may belong to multiple categories.

In such a scenario, the article’s link should appear in all relevant category lists.

Page Layout Integration

The Jinja2 navigation partial should be included in the base template so that every page automatically inherits it.

3. Non-Functional Requirements
Performance

The build process should be performant enough to handle a few hundred or thousand articles without excessive runtime.

Maintainability

The solution must be clear and documented so that developers can easily adjust or extend it.

The addition, removal, or renaming of categories or articles should not require rewriting the core generation logic.

Extensibility

Design the logic so that new features (e.g., date-based sorting, additional metadata) can be added without major refactoring.

Keep an eye on potential future needs (e.g., subcategories, tags, etc.).

Compatibility

Must seamlessly integrate with the existing Python-based static generator code.

Leverage existing Jinja2 best practices for partials, includes, or macros.

4. Technical Approach
Directory & File Structure

All content articles (Markdown files) stored in a content directory (or similar).

Each article file contains front matter in YAML (or JSON/TOML) specifying at least:

yaml
Copy
Edit
---
title: "Article Title"
category: "CategoryName"
slug: "article-title"
---
Or each article’s metadata could exist separately in a metadata file.

Metadata Parsing

Write or use existing Python code to:

Scan the content directory for files.

Extract front matter from each Markdown file (e.g., using a YAML/JSON parser).

Store the results in a Python structure such as:

python
Copy
Edit
articles = [
  {"title": "Article Title", "category": "CategoryName", "slug": "article-title", "content": "..."},
  ...
]
Category Mapping

Build a Python dictionary or default dictionary keyed by category name:

python
Copy
Edit
from collections import defaultdict

categories = defaultdict(list)
for article in articles:
    cat = article["category"]
    categories[cat].append({
        "title": article["title"],
        "url": "/{}".format(article["slug"]),  # Example URL pattern
    })
If multiple categories per article are allowed, parse them as a list and insert the article into each relevant category.

Navigation Template (Partial)

Create a dedicated Jinja2 template file for the navigation bar (e.g., templates/partials/navbar.html).

Within this file, write a loop to render categories and articles. Example snippet:

jinja2
Copy
Edit
<nav>
  <ul>
    {% for category, items in categories.items() %}
      <li>{{ category }}
        <ul>
          {% for article in items %}
            <li><a href="{{ article.url }}">{{ article.title }}</a></li>
          {% endfor %}
        </ul>
      </li>
    {% endfor %}
  </ul>
</nav>
Base Layout Integration

Create a main/base layout file (e.g., templates/base.html) that includes the navigation partial:

jinja2
Copy
Edit
<!DOCTYPE html>
<html>
  <head>
    <title>{{ page.title }}</title>
  </head>
  <body>
    {% include "partials/navbar.html" %}
    <main>
      {{ page.content | safe }}
    </main>
  </body>
</html>
Ensure that every generated page is rendered by this base.html with the required context (e.g., categories, page data).

Rendering Pages

For each article:

Create a Jinja2 context that contains both page (title, content, etc.) and categories from the global mapping.

Render the base.html template with this context, producing output/<slug>/index.html or any other preferred structure.

Regeneration

Ensure that the generator script re-scans the content directory each time it’s run.

Confirm that new or removed articles automatically update the categories dictionary.

Confirm that updated content is written to the output directory.

5. Deliverables
Code for Metadata Extraction

Python module or function that scans the content directory, parses front matter, and returns a list of article dictionaries.

Category Mapping Logic

A Python data structure (e.g., dictionary) mapping each category to a list of its articles.

Navigation Partial (partials/navbar.html)

A Jinja2 template file that loops through the categories dictionary to build navigation links.

Base Template (base.html)

Showcasing how the navigation partial is included and how individual articles are rendered within the main layout.

Build Script

A Python script that orchestrates:

Parsing the content and building categories.

Rendering each article with Jinja2.

Outputting final HTML files to output/ or a similar folder.

Documentation

A short README or Wiki explaining:

How to add new articles (metadata format, file location).

How the generator compiles the final site.

How navigation is automatically updated.

6. Acceptance Criteria
Correct Display

The navigation bar appears on all generated pages and displays categories plus article links as expected.

Automatic Updates

Adding a new article (with valid metadata) places it into the correct category without any manual changes to templates.

No Hardcoding

No need to manually edit HTML for each new category or article.

Performance

The static generation process completes efficiently for the expected volume of articles.