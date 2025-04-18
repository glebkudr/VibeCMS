import os
import asyncio
import logging
import json
from typing import List, Dict
from motor.motor_asyncio import AsyncIOMotorClient
from jinja2 import Environment, FileSystemLoader, select_autoescape, ChoiceLoader
import shutil
from bs4 import BeautifulSoup
import sys
from pathlib import Path

# --- Import Menu Data Fetcher ---
from generator.menu_data import fetch_menu_data # Changed to absolute import

# --- Global Logging Setup --- Start ---
def setup_logging():
    """
    Configures root logger with StreamHandler (INFO) and FileHandler (DEBUG).
    Call this once at the beginning of the script.
    """
    log_fmt = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
    date_fmt = '%Y-%m-%d %H:%M:%S'
    log_dir = Path("/app/logs") # Log directory outside static_output
    log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger() # Get the root logger
    # Clear existing handlers on the root logger to avoid duplicates if script is re-imported/re-run
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.setLevel(logging.DEBUG) # Set root level to lowest (DEBUG)

    # StreamHandler (stderr) - logs INFO and above
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter(log_fmt, datefmt=date_fmt))
    root_logger.addHandler(stream_handler)

    # --- FileHandler ---
    # FileHandler - logs DEBUG and above
    file_handler = logging.FileHandler(log_dir / "generator.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_fmt, datefmt=date_fmt))
    root_logger.addHandler(file_handler)
    # --- FileHandler ---

    print(f"--- Logging configured. Stream: DEBUG+, File: DEBUG+ ---", file=sys.stderr, flush=True)

# Setup logging immediately
setup_logging()

# Get logger for this module (will inherit root config)
logger = logging.getLogger(__name__)
# --- Global Logging Setup --- End ---

# Константы и настройки
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/mydatabase')
MONGO_DB = os.getenv('MONGO_DATABASE', 'mydatabase')
ARTICLES_COLLECTION = 'articles'
# Используем абсолютный путь, который будет смонтирован из хоста
STATIC_OUTPUT = '/app/static_output'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
MICROTEMPLATES_DIR = os.path.join(TEMPLATES_DIR, 'microtemplates')
SHARED_DIR = os.path.abspath(os.path.join(BASE_DIR, '../shared'))
MICROTEMPLATES_REGISTRY_PATH = os.path.join(SHARED_DIR, 'jinja_microtemplates.json')

# --- Load Micro-template Registry --- Start ---
def load_microtemplates_registry() -> Dict[str, Dict]:
    try:
        with open(MICROTEMPLATES_REGISTRY_PATH, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        logger.info(f"Successfully loaded micro-template registry from {MICROTEMPLATES_REGISTRY_PATH}")
        return registry
    except FileNotFoundError:
        logger.error(f"Micro-template registry file not found at {MICROTEMPLATES_REGISTRY_PATH}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {MICROTEMPLATES_REGISTRY_PATH}")
        return {}
    except Exception as e:
        logger.error(f"An unexpected error occurred loading the registry: {e}")
        return {}

microtemplates_registry = load_microtemplates_registry()
# --- Load Micro-template Registry --- End ---

# --- Jinja2 env Setup --- Start ---
# Use ChoiceLoader to look in both base templates and microtemplates directory
jinja_env = Environment(
    loader=ChoiceLoader([
        FileSystemLoader(TEMPLATES_DIR),
        FileSystemLoader(MICROTEMPLATES_DIR)
    ]),
    autoescape=select_autoescape(['html', 'xml']),
    auto_reload=True
)
# --- Jinja2 env Setup --- End ---

# --- Add Menu Data to Jinja2 Globals --- Start ---
async def update_jinja_globals(db: AsyncIOMotorClient) -> None:
    """Fetches dynamic data and updates Jinja2 environment globals."""
    logger.info("Fetching menu data for Jinja2 globals...")
    menu_data = await fetch_menu_data(db)
    jinja_env.globals["MENU_DATA"] = menu_data
    logger.info(f"Updated Jinja2 globals with {len(menu_data)} menu items.")
    logger.debug(f"MENU_DATA set in globals: {menu_data}") # DEBUG LOG ADDED
# --- Add Menu Data to Jinja2 Globals --- End ---

# Configure logger test
# logger.critical("!!! GENERATOR LOGGER CONFIGURED !!!") 

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

def process_microtemplates(content_html: str) -> str:
    """
    Finds <span data-jinja-tag=...> tags and replaces them with rendered microtemplates.
    """
    logger.critical(">>> ENTERING process_microtemplates") # DEBUG LOG ADDED
    logger.info("==> Entering process_microtemplates...")
    if not microtemplates_registry:
        logger.warning("Microtemplate registry is empty or failed to load. Skipping processing.")
        return content_html

    try:
        soup = BeautifulSoup(content_html, 'html.parser')
        jinja_spans = soup.find_all('span', attrs={'data-jinja-tag': True})

        if not jinja_spans:
            logger.info("No microtemplate tags found in content. Skipping processing.")
            return content_html

        logger.info(f"Found {len(jinja_spans)} microtemplate tags to process.")

        for span in jinja_spans:
            tag_name = span.get('data-jinja-tag')
            params_json = span.get('data-jinja-params', '{}')
            params = {}
            try:
                params = json.loads(params_json)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode params for tag '{tag_name}': {params_json}")

            if tag_name not in microtemplates_registry:
                logger.warning(f"Microtemplate '{tag_name}' found in HTML but not in registry. Skipping.")
                span.replace_with(f"<!-- Unknown microtemplate: {tag_name} -->")
                continue

            template_filename = microtemplates_registry[tag_name].get('template')
            if not template_filename:
                logger.warning(f"No template filename defined for microtemplate '{tag_name}' in registry. Skipping.")
                span.replace_with(f"<!-- Misconfigured microtemplate: {tag_name} (no template file) -->")
                continue

            try:
                logger.debug(f"Processing tag: {tag_name} with params: {params}")
                logger.debug(f"Attempting to load template: {template_filename}")
                template = jinja_env.get_template(template_filename)
                rendered_microtemplate = template.render(params)
                logger.debug(f"Rendered content for '{tag_name}':\n{rendered_microtemplate}")

                rendered_soup = BeautifulSoup(rendered_microtemplate, 'html.parser')

                logger.debug(f"Replacing span: {span}")
                if len(rendered_soup.contents) == 1 and rendered_soup.contents[0].name:
                    replacement_node = rendered_soup.contents[0]
                    span.replace_with(replacement_node)
                    logger.debug(f"Replaced with single node: {replacement_node}")
                else:
                    replacement_contents = rendered_soup.contents
                    span.replace_with(*replacement_contents)
                    logger.debug(f"Replaced with multiple nodes/text: {replacement_contents}")

            except Exception as e:
                logger.error(f"Error rendering/replacing microtemplate '{tag_name}' ({template_filename}): {e}", exc_info=True)
                span.replace_with(f"<!-- Error processing microtemplate: {tag_name} ({str(e)}) -->")

        final_html = soup.decode_contents()
        logger.info("<== Exiting process_microtemplates (processed)")
        return final_html

    except Exception as e:
        logger.error(f"Error processing microtemplates: {e}", exc_info=True)
        logger.info("<== Exiting process_microtemplates (error)")
        return content_html

def render_article_html(article: dict) -> str:
    """
    Render article HTML using stored HTML content and template,
    after processing microtemplates.
    """
    logger.critical(f">>> ENTERING render_article_html for slug: {article.get('slug')}") # DEBUG LOG ADDED
    logger.info(f"--> Entering render_article_html for slug: {article.get('slug')}")
    content_html = article.get('content_html', '')

    processed_content = process_microtemplates(content_html)
    logger.info("<-- Returned from process_microtemplates. Rendering main template...")

    template = jinja_env.get_template('article.html')
    html = template.render(
        title=article.get('title', 'Untitled'),
        content=processed_content,
        slug=article.get('slug', 'no-slug'),
        article=article
    )
    logger.info(f"<-- Exiting render_article_html for slug: {article.get('slug')}")
    return html

def copy_static_assets():
    """
    Copy static assets (CSS, JS) to static_output.
    (Currently only copies style.css)
    """
    # Correct path to the single CSS file in the templates directory
    src = os.path.join(TEMPLATES_DIR, 'style.css')
    dst = os.path.join(STATIC_OUTPUT, 'style.css')

    if not os.path.isfile(src):
        logger.warning(f"Static asset not found: {src}. Skipping copy.")
        return

    try:
        # Ensure the destination directory exists (root of STATIC_OUTPUT)
        os.makedirs(STATIC_OUTPUT, exist_ok=True)
        shutil.copyfile(src, dst)
        logger.info(f"Copied static asset: {src} to {dst}")
    except Exception as e:
        logger.error(f"Error copying static asset {src} to {dst}: {e}", exc_info=True)

async def generate():
    """
    Main generation logic: fetch articles, render, and write HTML files.
    """
    # The print statement below will now use the globally configured logger
    logger.info("Starting static site generation...") 

    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]
    # Ensure STATIC_OUTPUT exists before clearing (clear_static_output also does this)
    os.makedirs(STATIC_OUTPUT, exist_ok=True)
    clear_static_output() # Clear the output dir (log file is safe in /app/logs)

    # --- Fetch data and update Jinja2 globals ---
    await update_jinja_globals(db) # Added call to update globals
    logger.debug(f"Jinja globals after update: {list(jinja_env.globals.keys())}") # DEBUG LOG ADDED

    articles = await fetch_published_articles(db)
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

    # logging.shutdown() will be called implicitly on exit, or can be called if needed
    # print("--- GENERATOR SCRIPT FINISHED ---", file=sys.stderr, flush=True) # Removed debug print

if __name__ == '__main__':
    # Keep the try-except around asyncio.run for unhandled errors
    try:
        asyncio.run(generate())
    except Exception as main_err:
        # Use the configured logger to log the exception
        logger.critical(f"Generator failed with unhandled exception: {main_err}", exc_info=True)
        # Optionally print to stderr as well
        # print(f"!!! GENERATOR FAILED WITH UNCAUGHT EXCEPTION: {main_err} !!!", file=sys.stderr, flush=True)
        raise # Re-throw exception 