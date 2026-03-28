"""MongoDB collection access layer for unstructured and agentic data stores."""

from __future__ import annotations

from dataclasses import dataclass

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from pharma_os.db.mongo import get_mongo_database


@dataclass(frozen=True)
class MongoCollectionNames:
    """Canonical collection names used by PHARMA-OS."""

    clinical_notes: str = "clinical_notes"
    trial_criteria_docs: str = "trial_criteria_docs"
    literature_chunks: str = "literature_chunks"
    agent_memory: str = "agent_memory"
    agent_traces: str = "agent_traces"


COLLECTIONS = MongoCollectionNames()


def _collection(db: AsyncIOMotorDatabase, name: str) -> AsyncIOMotorCollection:
    return db.get_collection(name)


def get_clinical_notes_collection(db: AsyncIOMotorDatabase | None = None) -> AsyncIOMotorCollection:
    database = db or get_mongo_database()
    return _collection(database, COLLECTIONS.clinical_notes)


def get_trial_criteria_docs_collection(db: AsyncIOMotorDatabase | None = None) -> AsyncIOMotorCollection:
    database = db or get_mongo_database()
    return _collection(database, COLLECTIONS.trial_criteria_docs)


def get_literature_chunks_collection(db: AsyncIOMotorDatabase | None = None) -> AsyncIOMotorCollection:
    database = db or get_mongo_database()
    return _collection(database, COLLECTIONS.literature_chunks)


def get_agent_memory_collection(db: AsyncIOMotorDatabase | None = None) -> AsyncIOMotorCollection:
    database = db or get_mongo_database()
    return _collection(database, COLLECTIONS.agent_memory)


def get_agent_traces_collection(db: AsyncIOMotorDatabase | None = None) -> AsyncIOMotorCollection:
    database = db or get_mongo_database()
    return _collection(database, COLLECTIONS.agent_traces)
