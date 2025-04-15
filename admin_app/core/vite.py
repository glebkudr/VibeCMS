import json
import os
from pathlib import Path
from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment
import logging # Use logging

logger = logging.getLogger(__name__)

# Determine if running in development mode (Vite dev server is active)
# We can use an environment variable or check if manifest.json exists
VITE_DEV_MODE = os.getenv("VITE_DEV_MODE", "false").lower() == "true"
# Or check for manifest on startup (less flexible for switching without restart)
# MANIFEST_PATH = Path("admin_app/static/admin_dist/.vite/manifest.json")
# VITE_DEV_MODE = not MANIFEST_PATH.exists()

VITE_MANIFEST = {}
VITE_BASE_URL = os.getenv("VITE_DEV_SERVER_URL", "http://localhost:5173") # Vite dev server default, allow override

# Read manifest in production mode
if not VITE_DEV_MODE:
    # Correct path relative to the project root where FastAPI runs
    manifest_path = Path("admin_app/static/admin_dist/.vite/manifest.json")
    logger.info(f"Looking for Vite manifest at: {manifest_path.resolve()}")
    if manifest_path.exists():
        try:
            with open(manifest_path, "r") as f:
                VITE_MANIFEST = json.load(f)
            logger.info("Vite manifest loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading Vite manifest: {e}", exc_info=True)
            VITE_MANIFEST = {} # Ensure it's a dict even on error
    else:
        logger.warning(f"Vite manifest not found at {manifest_path}. Production assets might be unavailable.")
else:
    logger.info(f"Vite running in development mode. Expecting assets from {VITE_BASE_URL}")


def generate_vite_tags(entry_point: str = "src/main.ts") -> str:
    """
    Generates <script> and <link> tags for Vite assets.

    Args:
        entry_point: The main entry point file (e.g., 'src/main.ts').

    Returns:
        HTML string with the necessary tags.
    """
    if VITE_DEV_MODE:
        # Development mode: Include Vite client and entry point directly from dev server
        # Ensure the base URL ends with a slash
        base_url = VITE_BASE_URL.rstrip('/') + '/'
        logger.debug(f"Generating Vite dev tags for {entry_point} from {base_url}")
        return f"""
            <script type="module" src="{base_url}@vite/client"></script>
            <script type="module" src="{base_url}{entry_point}"></script>
        """
    else:
        # Production mode: Use manifest.json
        tags = ""
        entry_data = VITE_MANIFEST.get(entry_point)

        if not entry_data:
            logger.error(f"Entry point '{entry_point}' not found in Vite manifest.")
            return ""

        # Add CSS links
        if "css" in entry_data:
            for css_file in entry_data["css"]:
                tags += f'<link rel="stylesheet" href="/static/admin_dist/{css_file}">\n'

        # Add JS script tag
        if "file" in entry_data:
            js_file = entry_data["file"]
            tags += f'<script type="module" src="/static/admin_dist/{js_file}"></script>\n'
        else:
            logger.error(f"JS file not found for entry point '{entry_point}' in Vite manifest.")

        # Handle imports (preload, etc.) - might need refinement based on actual manifest structure
        # This part is simplified; real-world scenarios might need more robust preload/prefetch logic
        # if "imports" in entry_data:
        #     for imp_key in entry_data["imports"]:
        #         imp_data = VITE_MANIFEST.get(imp_key, {})
        #         if imp_data.get("file"):
        #             tags += f'<link rel="modulepreload" href="/static/admin_dist/{imp_data["file"]}">\n'

        logger.debug(f"Generated Vite production tags for {entry_point}:\n{tags}")
        return tags

def register_vite_env(env: Environment):
    """Registers the vite_tags function as a global in Jinja2 environment."""
    env.globals['vite_tags'] = generate_vite_tags
    logger.info("Registered 'vite_tags' function in Jinja2 environment.") 