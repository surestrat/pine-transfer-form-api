import os
import sys
import uvicorn
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def verify_schema_exists():
    """
    Verify that the Appwrite schema file exists, create a sample if it doesn't.
    """
    schema_path = project_root / "appwrite-schema.json"

    if not schema_path.exists():
        print("Warning: appwrite-schema.json not found. Creating a sample schema.")
        sample_schema = {
            "collectionName": "pineapple-lead-transfer-col-id",
            "databaseId": "pineapple-lead-transfer-id",
            "attributes": [
                {"key": "first_name", "type": "string", "size": 100, "required": True},
                # ...other attributes
            ],
        }

        with open(schema_path, "w") as f:
            json.dump(sample_schema, f, indent=2)

        print(f"Created sample schema at {schema_path}")
        print("Please update this file with your actual schema configuration.")


if __name__ == "__main__":
    try:
        # Verify schema file exists
        verify_schema_exists()

        print("Starting Pine API server...")
        # Start the server with the app from the app package
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 4000)),
            reload=True,
            log_level="info",
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
