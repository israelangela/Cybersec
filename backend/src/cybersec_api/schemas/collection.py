from uuid import UUID

from pydantic import BaseModel


class SourceCollectionResult(BaseModel):
    source_id: UUID
    source_name: str
    status: str
    fetched: int = 0
    created: int = 0
    duplicates: int = 0
    skipped: int = 0
    error: str | None = None


class CollectionRunResult(BaseModel):
    status: str
    sources_checked: int
    fetched: int
    created: int
    duplicates: int
    skipped: int
    errors: int
    results: list[SourceCollectionResult]
