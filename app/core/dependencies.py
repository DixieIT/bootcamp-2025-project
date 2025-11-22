"""Shared dependencies for the application."""

from app.services.prompt_store import DatabaseStore, FileSnapshotStore, InMemoryStore
from app.core.config import settings

# Singleton store instance - shared across all routers
if settings.USE_DATABASE:
    store = DatabaseStore(settings.DATABASE_PATH)
elif settings.FILE_SNAPSHOT:
    store = FileSnapshotStore("var/data.json")
else:
    store = InMemoryStore()
