import logging

import datetime

from uuid import uuid4

from appwrite.client import Client

from config.settings import settings

from typing import Dict, Any, Optional

from appwrite.exception import AppwriteException

from appwrite.services.databases import Databases

from appwrite.query import Query

logger = logging.getLogger("pineapple-surestrat-api")


def safe_uuid():
    return str(uuid4()).replace("-", "")


def get_appwrite_client():
    client = Client()

    logger.info(
        f"Initializing Appwrite client with endpoint: {settings.APPWRITE_ENDPOINT}"
    )
    logger.info(f"Using project ID: {settings.APPWRITE_PROJECT_ID}")

    if (
        not settings.APPWRITE_ENDPOINT
        or not settings.APPWRITE_PROJECT_ID
        or not settings.APPWRITE_API_KEY
    ):
        error_msg = "Appwrite configuration missing:"
        if not settings.APPWRITE_ENDPOINT:
            error_msg += " ENDPOINT"
        if not settings.APPWRITE_PROJECT_ID:
            error_msg += " PROJECT_ID"
        if not settings.APPWRITE_API_KEY:
            error_msg += " API_KEY"
        logger.error(error_msg)
        raise ValueError(error_msg)

    client.set_endpoint(settings.APPWRITE_ENDPOINT)
    client.set_project(settings.APPWRITE_PROJECT_ID)
    client.set_key(settings.APPWRITE_API_KEY)

    logger.debug("Appwrite client successfully configured")
    return client


def get_database():
    """Get the Appwrite database service instance"""
    client = get_appwrite_client()
    return Databases(client)


async def get_server_timestamp():
    try:
        response = datetime.datetime.now(datetime.timezone.utc)
        return response
    except Exception as e:
        logger.error(f"Error getting server timestamp: {str(e)}")
        raise


def _prepare_data_for_appwrite(data: Dict[str, Any]) -> Dict[str, Any]:
    result = {}
    for key, value in data.items():
        if isinstance(value, datetime.datetime):
            result[key] = value.isoformat()
        elif isinstance(value, datetime.date):
            result[key] = value.isoformat()
        elif value is None:
            continue
        else:
            result[key] = value
    return result


class AppwriteService:
    def __init__(self, database_id: Optional[str] = None):
        self.database: Databases = get_database()
        self.database_id: str = database_id or settings.DATABASE_ID or ""
        self.transfer_collection_id: str | None = settings.TRANSFER_COL_ID
        self.quote_collection_id: str | None = settings.QUOTE_COL_ID

        if not self.database_id:
            logger.error(
                "APPWRITE_DATABASE_ID not set in environment variables or constructor"
            )
            raise ValueError("APPWRITE_DATABASE_ID must be set")

        logger.info(f"AppwriteService initialized with database_id: {self.database_id}")

        if self.transfer_collection_id:
            logger.info(f"transfer collection_id: {self.transfer_collection_id}")
        if self.quote_collection_id:
            logger.info(f"Quote collection_id: {self.quote_collection_id}")

    def create_document(
        self, data: dict, collection_type: str, document_id: Optional[str] = None
    ):
        try:
            collection_id = self._get_collection_id(collection_type)
            if not collection_id:
                raise ValueError(f"Unknown collection type: {collection_type}")

            document_id = document_id or safe_uuid()
            try:
                prepared_data = _prepare_data_for_appwrite(data)

                result = self.database.create_document(
                    database_id=self.database_id,
                    collection_id=collection_id,
                    document_id=document_id,
                    data=prepared_data,
                )

                return {"$id": document_id, "data": result, "success": True}
            except AppwriteException as ae:
                return {"error": str(ae)}

        except Exception as e:
            logger.error(f"Error in create_document: {str(e)}")
            return {"error": str(e)}

    def update_document(
        self,
        document_id: str,
        data: dict,
        collection_type: str,
    ):

        col_id = self._get_collection_id(collection_type)
        if not col_id:
            return {"error": f"Unknown collection type: {collection_type}"}
        try:
            prepared_data = _prepare_data_for_appwrite(data)
            result = self.database.update_document(
                database_id=self.database_id,
                collection_id=col_id,
                document_id=document_id,
                data=prepared_data,
            )

            return {"$id": document_id, "data": result, "success": True}

        except AppwriteException as ae:
            return {"error": str(ae)}
        except Exception as e:
            return {"error": str(e)}

    def search_documents(
        self,
        collection_type: str,
        search_query: str,
        fields: Optional[list[str]] = None,
    ):
        col_id = self._get_collection_id(collection_type)
        try:
            queries = [Query.search("source", search_query)]
            if fields:
                queries.append(Query.select(fields))
            params = {
                "database_id": self.database_id,
                "collection_id": col_id,
                "queries": queries,
            }
            result = self.database.list_documents(**params)
            return result
        except Exception as e:
            return e

    def list_documents(self, collection_type: str, fields: Optional[list[str]] = None):
        col_id = self._get_collection_id(collection_type)
        try:
            queries = []
            if fields:
                queries.append(Query.select(fields))
            params = {
                "database_id": self.database_id,
                "collection_id": col_id,
            }
            if queries:
                params["queries"] = str(queries)
            result = self.database.list_documents(**params)
            return result
        except AppwriteException as ae:
            return {f"error: {ae}"}

    def get_document_by_id(
        self,
        collection_type: str,
        document_id: str,
        request_id: Optional[str] = None,
    ):
        req_id = request_id or safe_uuid()
        col_id = self._get_collection_id(collection_type)

        if not col_id:
            logger.error(f"[{req_id}] Unknown collection type: {collection_type}")
            return {"error": f"Unknown collection type: {collection_type}"}

        try:
            result = self.database.get_document(
                database_id=self.database_id,
                collection_id=col_id,
                document_id=document_id,
            )
            return {"data": result}
        except AppwriteException as ae:
            logger.error(f"[{req_id}] Appwrite get_document failed: {str(ae)}")
            return {"error": str(ae)}

    def _get_collection_id(self, collection_type: str):

        if collection_type == "transfer":
            return self.transfer_collection_id
        elif collection_type == "quote":
            return self.quote_collection_id
        else:
            return None
