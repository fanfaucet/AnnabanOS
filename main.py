from fastapi import FastAPI

from api.actor_endpoints import router as actor_router
from api.input_endpoints import router as input_router
from api.provider_endpoints import router as provider_router
from api.stream_endpoints import router as stream_router

app = FastAPI(title="AnnabanOS Model Provider and Thread API")
app.include_router(provider_router)
app.include_router(actor_router)
app.include_router(input_router)
app.include_router(stream_router)
