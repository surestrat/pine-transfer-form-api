import os
import sys
import uvicorn
import logging
import traceback
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def clean_pycache(dir):
    """
    Recursively remove all __pycache__ directories in the given directory.
    """
    for root, dirs, files in os.walk(dir):
        if "__pycache__" in dirs or "__pycache__" in files:
            pycache_path = Path(root) / "__pycache__"
            try:
                for file in pycache_path.glob("*.pyc"):
                    file.unlink()
                pycache_path.rmdir()
                print(f"Removed: {pycache_path}")
            except Exception as e:
                print(f"Error removing {pycache_path}: {e}")


if __name__ == "__main__":
    try:
        clean_pycache(".")
        print("Cleaned __pycache__ directories.")
        from dotenv import load_dotenv

        load_dotenv()

        logging.basicConfig(
            level=(
                logging.DEBUG
                if os.getenv("DEBUG", "false").lower() == "true"
                else logging.INFO
            ),
            format="[%(asctime)s] - %(levelname)s - %(message)s",
            datefmt="%Y/%m/%d %H:%M:%S",
        )

        logger = logging.getLogger("Pineapple-surestrat-api")
        logger.info("Starting Pineapple-surestrat-api...")

        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 4000)),
            reload=True,
            log_level=str(os.environ.get("LOG_LEVEL", "debug")).lower(),
            log_config=None,
        )
    except Exception as e:
        print(f"An error occurred while starting the server: {e}")
        traceback.print_exc()
        sys.exit(1)
