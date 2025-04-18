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
    Converts a MongoDB document's `_id` (ObjectId) to a string
    BEFORE validating against the provided Pydantic model.

    Args:
        doc: The dictionary retrieved from MongoDB.
        model_cls: The Pydantic model class to validate against.

    Returns:
        An instance of the Pydantic model.

    Raises:
        ValueError: If the document fails Pydantic validation or `_id` is missing.
    """
    if not doc or "_id" not in doc:
        raise ValueError(f"Document is missing expected '_id' field for model {model_cls.__name__}")

    # Work on a copy to avoid modifying the original dictionary
    processed_doc = doc.copy()

    # Convert ObjectId to string directly in the _id field of the copy
    if isinstance(processed_doc["_id"], ObjectId):
        processed_doc["_id"] = str(processed_doc["_id"])
    # If _id is already something else, try converting to string anyway
    elif not isinstance(processed_doc["_id"], str):
        try:
            processed_doc["_id"] = str(processed_doc["_id"])
        except Exception as conversion_err:
            raise ValueError(f"Could not convert '_id' field to string for model {model_cls.__name__}: {conversion_err}") from conversion_err

    # Now _id in processed_doc should be a string, compatible with TagRead's id field alias

    try:
        # Validate the processed document against the Pydantic model
        validated_model = model_cls(**processed_doc)
        return validated_model
    except Exception as e: # Catch Pydantic's ValidationError and potentially others
        doc_id_repr = processed_doc.get("_id", "N/A") # Use _id from processed doc
        logger.error(f"Pydantic validation failed for doc {doc_id_repr} against model {model_cls.__name__}: {e}")
        raise ValueError(f"Data validation failed for model {model_cls.__name__}: {e}") from e 