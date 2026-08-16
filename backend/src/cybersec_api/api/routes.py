from fastapi import APIRouter

from cybersec_api.api.collection import router as collection_router
from cybersec_api.api.enrichment import router as enrichment_router
from cybersec_api.api.intelligence import router as intelligence_router
from cybersec_api.api.items import router as items_router
from cybersec_api.api.normalization import router as normalization_router
from cybersec_api.api.sources import router as sources_router
from cybersec_api.api.stories import router as stories_router
from cybersec_api.api.system import router as system_router

router = APIRouter()
router.include_router(system_router)
router.include_router(sources_router)
router.include_router(items_router)
router.include_router(collection_router)
router.include_router(normalization_router)
router.include_router(enrichment_router)
router.include_router(intelligence_router)
router.include_router(stories_router)
