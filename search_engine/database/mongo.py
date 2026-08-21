"""MongoDB connection helper."""

from __future__ import annotations

from pymongo import MongoClient
from pymongo.database import Database

from search_engine.config import SearchEngineConfig


class MongoConnection:
    """Create a configured MongoDB client and database handle."""

    def __init__(self, config: SearchEngineConfig):
        if not config.mongo_uri:
            raise RuntimeError(
                "MONGO_URI is not set. Copy .env.example to .env and add your MongoDB URI."
            )

        self.client = MongoClient(config.mongo_uri, serverSelectionTimeoutMS=10000)
        self.db: Database = self.client[config.mongo_db_name]

    def ping(self) -> None:
        self.client.admin.command("ping")

    def close(self) -> None:
        self.client.close()
