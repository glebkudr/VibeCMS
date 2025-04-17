"""
admin_app/core/utils.py

Utility functions for the admin application.
"""

import logging
from typing import Type, TypeVar, Dict, Any
from pydantic import BaseModel
from bson import ObjectId

logger = logging.getLogger(__name__)

# Generic TypeVar for Pydantic models
M = TypeVar("M", bound=BaseModel)

def convert_objectid_to_str(doc: Dict[str, Any], model_cls: Type[M]) -> M:
    """
    Converts a MongoDB document's `_id` (ObjectId) to a string `id`
    and validates the document against the provided Pydantic model.

    Args:
        doc: The dictionary retrieved from MongoDB.
        model_cls: The Pydantic model class to validate against.

    Returns:
        An instance of the Pydantic model.

    Raises:
        ValueError: If the document fails Pydantic validation.
        KeyError: If `_id` is missing (though less likely with MongoDB).
    """
    if "_id" in doc and isinstance(doc["_id"], ObjectId):
        doc["id"] = str(doc["_id"])
        # del doc["_id"] # Keep _id for potential internal use?
                        # Pydantic models usually ignore extra fields unless configured otherwise
    elif "_id" in doc:
        # If _id is already a string or other type, ensure it's assigned to id if id isn't already set
        if "id" not in doc:
            doc["id"] = str(doc["_id"]) # Ensure it's a string

    try:
        # Validate the potentially modified document against the Pydantic model
        # This will raise ValidationError if fields are missing or types are wrong
        validated_model = model_cls(**doc)
        return validated_model
    except Exception as e: # Catch Pydantic's ValidationError and potentially others
        doc_id_repr = doc.get("id", doc.get("_id", "N/A"))
        logger.error(f"Pydantic validation failed for doc {doc_id_repr} against model {model_cls.__name__}: {e}")
        # Re-raise the validation error to be handled by the caller (e.g., FastAPI)
        # Or raise a specific HTTP exception if preferred
        raise ValueError(f"Data validation failed for model {model_cls.__name__}: {e}") from e 