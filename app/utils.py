import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("pine-api")


def load_appwrite_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the Appwrite schema from a JSON file.

    Args:
        schema_path: Path to the schema file. If None, uses default location.

    Returns:
        Dictionary containing the schema information
    """
    if schema_path is None:
        # Get the parent directory of the current file (app directory)
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        schema_path = os.path.join(app_dir, "appwrite-schema.json")

    try:
        with open(schema_path, "r") as f:
            schema = json.load(f)
        return schema
    except Exception as e:
        logger.error(f"Error loading Appwrite schema: {e}")
        return {"attributes": []}


def validate_data_against_schema(
    data: Dict[str, Any], schema_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate and transform data to match the Appwrite schema.

    Args:
        data: The data to validate
        schema_path: Path to the schema file. If None, uses default location.

    Returns:
        Dictionary containing validated data that matches the schema
    """
    schema = load_appwrite_schema(schema_path)
    valid_data = {}

    # Create a mapping of attribute keys to their types and constraints
    attr_map = {attr["key"]: attr for attr in schema.get("attributes", [])}

    for key, value in data.items():
        if key in attr_map:
            attr = attr_map[key]

            # Handle different types
            if attr["type"] == "string":
                # Convert to string if not already and check size
                str_value = str(value) if value is not None else ""
                max_size = attr.get("size", 100)

                if len(str_value) > max_size:
                    logger.warning(
                        f"Value for '{key}' exceeds max size of {max_size}. Truncating."
                    )
                    str_value = str_value[:max_size]

                valid_data[key] = str_value
            else:
                # Handle other types as needed
                valid_data[key] = value

    # Check for required fields
    for attr in schema.get("attributes", []):
        if attr.get("required", False) and attr["key"] not in valid_data:
            logger.warning(f"Required field '{attr['key']}' is missing")

    return valid_data


def prepare_api_response_for_storage(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare API response data for storage in Appwrite.

    Args:
        api_response: The API response to prepare

    Returns:
        Dictionary containing data ready for storage
    """
    storage_data = {}

    # Store full response as JSON string
    storage_data["api_response_str"] = json.dumps(api_response, default=str)

    # Extract specific fields
    if api_response.get("success") and isinstance(api_response.get("data"), dict):
        data = api_response["data"]
        if "uuid" in data:
            storage_data["uuid"] = data["uuid"]
        if "redirect_url" in data:
            storage_data["redirect_url"] = data["redirect_url"]

    return storage_data
