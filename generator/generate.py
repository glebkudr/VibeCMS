import os
import asyncio
import logging
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Константы и настройки
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/mydatabase')
MONGO_DB = os.getenv('MONGO_DATABASE', 'mydatabase')
ARTICLES_COLLECTION = 'articles'
STATIC_OUTPUT = 'static_output'
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')

# Jinja2 env
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)

md = MarkdownIt()

async def fetch_published_articles(db) -> List[dict]:
    """
    Fetch all published articles from MongoDB.
    """
    articles = await db[ARTICLES_COLLECTION].find({'status': 'published'}).to_list(length=None)
    logger.info(f"Fetched {len(articles)} published articles from DB.")
    return articles

def clear_static_output():
    """
    Remove all contents from the static_output directory.
    """
    if os.path.exists(STATIC_OUTPUT):
        for root, dirs, files in os.walk(STATIC_OUTPUT, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
    else:
        os.makedirs(STATIC_OUTPUT, exist_ok=True)
    logger.info(f"Cleared {STATIC_OUTPUT}/ directory.")

def render_article_html(article: dict) -> str:
    """
    Render article HTML from markdown and template.
    """
    content_html = md.render(article['content_md'])
    template = jinja_env.get_template('article.html')
    html = template.render(
        title=article['title'],
        content=content_html,
        slug=article['slug'],
        article=article
    )
    return html

async def generate():
    """
    Main generation logic: fetch articles, render, and write HTML files.
    """
    logger.info("Starting static site generation...")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]
    articles = await fetch_published_articles(db)
    clear_static_output()
    for article in articles:
        html = render_article_html(article)
        out_dir = os.path.join(STATIC_OUTPUT, article['slug'])
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'index.html')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        logger.info(f"Generated {out_path}")
    logger.info("Static site generation complete.")

if __name__ == '__main__':
    asyncio.run(generate()) 