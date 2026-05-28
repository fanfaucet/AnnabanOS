from fastapi import FastAPI

from api.stream_endpoints import router as stream_router
from api.ui_endpoints import router as ui_router

app = FastAPI(title="AnthropicAI MVP v2.0")
app.include_router(ui_router)
app.include_router(stream_router)
