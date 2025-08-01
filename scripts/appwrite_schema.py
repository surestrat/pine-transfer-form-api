import logging
import time
from appwrite.exception import AppwriteException
from appwrite.services.databases import Databases
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))



def log_and_create_attribute(create_func, *args, **kwargs):
    try:
        logging.info(f"Creating attribute/index: {kwargs.get('key', args[2] if len(args) > 2 else 'unknown')} ({create_func.__name__})")
        result = create_func(*args, **kwargs)
        logging.info(f"Successfully created: {kwargs.get('key', args[2] if len(args) > 2 else 'unknown')}")
        return result
    except AppwriteException as ae:
        logging.warning(f"AppwriteException during creation: {ae}")
        return None
    except Exception as e:
        logging.error(f"Exception during creation: {e}")
        return None


def list_collection_attributes(db, database_id, collection_id):
    try:
        attrs = db.list_attributes(database_id=database_id, collection_id=collection_id)
        logging.info(f"Attributes for collection {collection_id}: {[a['key'] for a in attrs['attributes']]}")
        return attrs
    except Exception as e:
        logging.error(f"Error listing attributes: {e}")
        return None

def init_transfer_schema(db, database_id, transfer_collection_id):
    try:
        log_and_create_attribute(db.create_string_attribute, database_id, transfer_collection_id, key="first_name", size=30, required=True)
        log_and_create_attribute(db.create_string_attribute, database_id, transfer_collection_id, key="last_name", size=30, required=True)
        log_and_create_attribute(db.create_string_attribute, database_id, transfer_collection_id, key="email", size=255, required=True)
        log_and_create_attribute(db.create_string_attribute, database_id, transfer_collection_id, key="id_number", size=13, required=False)
        log_and_create_attribute(db.create_string_attribute, database_id, transfer_collection_id, key="quote_id", size=50, required=False)
        log_and_create_attribute(db.create_string_attribute, database_id, transfer_collection_id, key="contact_number", size=15, required=True)
        log_and_create_attribute(db.create_string_attribute, database_id, transfer_collection_id, key="uuid", size=255, required=False)
        log_and_create_attribute(db.create_string_attribute, database_id, transfer_collection_id, key="redirect_url", size=255, required=False)
        log_and_create_attribute(db.create_string_attribute, database_id, transfer_collection_id, key="agent_name", size=30, required=True)
        log_and_create_attribute(db.create_string_attribute, database_id, transfer_collection_id, key="branch_name", size=30, required=True)
        log_and_create_attribute(db.create_index, database_id, transfer_collection_id, key="unique_email", type="unique", attributes=["email"])
        log_and_create_attribute(db.create_index, database_id, transfer_collection_id, key="unique_contact_number", type="unique", attributes=["contact_number"])
        log_and_create_attribute(db.create_index, database_id, transfer_collection_id, key="unique_id_number", type="unique", attributes=["id_number"])
        log_and_create_attribute(db.create_index, database_id, transfer_collection_id, key="idx_email", type="fulltext", attributes=["email"])
        log_and_create_attribute(db.create_index, database_id, transfer_collection_id, key="idx_contact_number", type="fulltext", attributes=["contact_number"])
        logging.info("Successfully initialized transfer attributes with unique constraints.")
    except Exception as e:
        logging.error(f"Error in init_transfer_schema: {e}")

def init_quote_schema(db, database_id, quote_collection_id):
    try:
        log_and_create_attribute(
            db.create_string_attribute,
            database_id,
            quote_collection_id,
            key="source",
            size=50,
            required=True
        )
        log_and_create_attribute(
            db.create_string_attribute,
            database_id,
            quote_collection_id,
            key="externalReferenceId",
            size=50,
            required=True
        )
        log_and_create_attribute(
            db.create_string_attribute,
            database_id,
            quote_collection_id,
            key="vehicles",
            size=10000,  # large enough to store JSON string
            required=True
        )
        logging.info("Successfully initialized quote attributes for vehicles as string.")
    except Exception as e:
        logging.error(f"Error in init_quote_schema: {e}")

async def main():
    import sys
    from pathlib import Path
    from dotenv import load_dotenv
    from app.utils.appwrite import AppwriteService
    from config.settings import settings

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    load_dotenv()

    logging.basicConfig(level=logging.INFO)

    appwrite_service = AppwriteService()
    db: Databases = appwrite_service.database

    database_id = settings.DATABASE_ID
    quote_collection_id = settings.QUOTE_COL_ID
    transfer_collection_id = settings.TRANSFER_COL_ID

    if not database_id or not quote_collection_id or not transfer_collection_id:
        logging.error("Missing required database or collection IDs")
        logging.error(f"Database ID: {database_id}")
        logging.error(f"Quote Collection ID: {quote_collection_id}")
        logging.error(f"Transfer Collection ID: {transfer_collection_id}")
        sys.exit(1)

    logging.info(f"Using database_id: {database_id}")
    logging.info(f"Using quote_collection_id: {quote_collection_id}")
    logging.info(f"Using transfer_collection_id: {transfer_collection_id}")

    init_transfer_schema(db, database_id, transfer_collection_id)
    init_quote_schema(db, database_id, quote_collection_id)
    logging.info("Waiting 10 seconds for Appwrite attribute propagation...")
    time.sleep(10)
    list_collection_attributes(db, database_id, transfer_collection_id)
    list_collection_attributes(db, database_id, quote_collection_id)
    logging.info("Schema initialization complete.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
