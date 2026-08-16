from pydantic import BaseModel

from cybersec_api.schemas.intelligence import CyberEntityAggregateRead, CyberEntityRead
from cybersec_api.schemas.item import ItemRead
from cybersec_api.schemas.story import StoryRead


class ExternalReferenceRead(BaseModel):
    label: str
    url: str


class CyberEntityContextRead(BaseModel):
    entity: CyberEntityAggregateRead
    items: list[ItemRead]
    stories: list[StoryRead]
    external_references: list[ExternalReferenceRead]


class ItemContextRead(BaseModel):
    item: ItemRead
    entities: list[CyberEntityRead]
    stories: list[StoryRead]
