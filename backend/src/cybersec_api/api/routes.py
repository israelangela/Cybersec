from fastapi import APIRouter

from cybersec_api.api.sources import router as sources_router
from cybersec_api.api.system import router as system_router

router = APIRouter()
router.include_router(system_router)
router.include_router(sources_router)
