from supabase import create_client, Client
from config.settings import settings
from app.utils.rich_logger import get_rich_logger
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = get_rich_logger("supabase")

class SupabaseClient:
    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
        logger.info("Supabase client initialized")

    def create_document(self, table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new document in the specified table"""
        try:
            response = self.client.table(table).insert(data).execute()
            if response.data:
                logger.info(f"Document created in {table}: {response.data[0].get('id')}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error creating document in {table}: {str(e)}")
            raise

    def update_document(self, table: str, document_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a document by ID"""
        try:
            # Remove created_at if present (it's immutable)
            if 'created_at' in data:
                del data['created_at']
            
            # Set updated_at to current timestamp
            data['updated_at'] = datetime.utcnow().isoformat()
            
            response = self.client.table(table).update(data).eq('id', document_id).execute()
            if response.data:
                logger.info(f"Document updated in {table}: {document_id}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating document {document_id} in {table}: {str(e)}")
            raise

    def get_document(self, table: str, document_id: int) -> Optional[Dict[str, Any]]:
        """Get a document by ID"""
        try:
            response = self.client.table(table).select("*").eq('id', document_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting document {document_id} from {table}: {str(e)}")
            raise

    def find_documents(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find documents by filters"""
        try:
            query = self.client.table(table).select("*")
            
            for field, value in filters.items():
                query = query.eq(field, value)
            
            response = query.execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error finding documents in {table}: {str(e)}")
            raise

    def check_duplicate_transfer(self, id_number: str, contact_number: str) -> Optional[Dict[str, Any]]:
        """Check for duplicate transfers by ID number or contact number"""
        try:
            # Normalize the inputs
            normalized_id = id_number.replace(" ", "").replace("-", "").replace("+", "") if id_number else ""
            normalized_contact = contact_number.replace(" ", "").replace("-", "").replace("+", "") if contact_number else ""
            
            logger.info(f"Checking for duplicates - ID: {normalized_id}, Contact: {normalized_contact}")
            
            # Check by ID number first
            if normalized_id:
                response = self.client.table('leads').select("*").ilike('id_number', f"%{normalized_id}%").execute()
                if response.data and len(response.data) > 0:
                    logger.info(f"Found duplicate transfer by ID number: {normalized_id}")
                    return response.data[0]
            
            # Check by contact number
            if normalized_contact:
                response = self.client.table('leads').select("*").ilike('contact_number', f"%{normalized_contact}%").execute()
                if response.data and len(response.data) > 0:
                    logger.info(f"Found duplicate transfer by contact number: {normalized_contact}")
                    return response.data[0]
            
            logger.info("No duplicate transfer found")
            return None
        except Exception as e:
            logger.error(f"Error checking for duplicate transfer: {str(e)}")
            raise

# Global instance
supabase_client = SupabaseClient()
