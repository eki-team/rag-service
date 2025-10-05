"""
MongoDB Configuration for Scientific Document Ingestion
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Optional
import os


class MongoConfig:
    """MongoDB configuration and connection management"""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        database_name: str = "rag_service"
    ):
        """
        Initialize MongoDB configuration
        
        Args:
            connection_string: MongoDB connection string (defaults to env var MONGO_URI)
            database_name: Database name
        """
        self.connection_string = connection_string or os.getenv(
            "MONGO_URI",
            "mongodb://localhost:27017/"
        )
        self.database_name = database_name
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None

    def connect(self) -> Database:
        """
        Connect to MongoDB and return database instance
        
        Returns:
            Database instance
        """
        if self._client is None:
            self._client = MongoClient(self.connection_string)
            self._db = self._client[self.database_name]
            
            # Create indexes
            self._create_indexes()
        
        return self._db

    def get_documents_collection(self) -> Collection:
        """Get documents collection"""
        db = self.connect()
        return db["documents"]

    def get_chunks_collection(self) -> Collection:
        """Get chunks collection"""
        db = self.connect()
        return db["chunks"]

    def _create_indexes(self):
        """Create indexes for efficient querying"""
        db = self.connect()
        
        # Documents collection indexes
        docs = db["documents"]
        docs.create_index([("pk", ASCENDING)], unique=True)
        docs.create_index([("publication_year", DESCENDING)])
        docs.create_index([("metadata.article_metadata.doi", ASCENDING)])
        docs.create_index([("metadata.article_metadata.pmc_id", ASCENDING)])
        docs.create_index([("created_at", DESCENDING)])
        
        # Chunks collection indexes
        chunks = db["chunks"]
        chunks.create_index([("pk", ASCENDING)], unique=True)
        chunks.create_index([("chunk_index", ASCENDING)])
        chunks.create_index([("verification.status", ASCENDING)])
        chunks.create_index([("created_at", DESCENDING)])

    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None


# Global instance
_mongo_config: Optional[MongoConfig] = None


def get_mongo_config() -> MongoConfig:
    """Get global MongoDB configuration instance"""
    global _mongo_config
    if _mongo_config is None:
        _mongo_config = MongoConfig()
    return _mongo_config


def get_documents_collection() -> Collection:
    """Get documents collection (convenience function)"""
    config = get_mongo_config()
    return config.get_documents_collection()


def get_chunks_collection() -> Collection:
    """Get chunks collection (convenience function)"""
    config = get_mongo_config()
    return config.get_chunks_collection()
