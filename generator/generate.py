import os
import asyncio
import logging
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from jinja2 import Environment, FileSystemLoader, select_autoescape
import shutil

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Константы и настройки
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/mydatabase')
MONGO_DB = os.getenv('MONGO_DATABASE', 'mydatabase')
ARTICLES_COLLECTION = 'articles'
# Используем абсолютный путь, который будет смонтирован из хоста
STATIC_OUTPUT = '/app/static_output'
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')

# Jinja2 env
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)

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
    Render article HTML using stored HTML content and template.
    """
    # Use content_html directly, ensure it exists or provide fallback
    content_html = article.get('content_html', '')
    template = jinja_env.get_template('article.html')
    html = template.render(
        title=article.get('title', 'Untitled'), # Use .get for safety
        content=content_html,
        slug=article.get('slug', 'no-slug'), # Use .get for safety
        article=article # Pass the full article dict for potential use in template
    )
    return html

def copy_static_assets():
    """
    Copy static assets (CSS, JS) to static_output.
    """
    src = os.path.join(TEMPLATES_DIR, 'style.css')
    dst = os.path.join(STATIC_OUTPUT, 'style.css')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    logger.info(f"Copied static asset: {dst}")

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
    copy_static_assets()
    logger.info("Static site generation complete.")

if __name__ == '__main__':
    asyncio.run(generate()) 