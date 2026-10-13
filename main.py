from fastapi import FastAPI

from api.provider_endpoints import router as provider_router
from api.stream_endpoints import router as stream_router

app = FastAPI(title="AnnabanOS Community Model API")
app.include_router(provider_router)
app.include_router(stream_router)
