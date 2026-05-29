from fastapi import FastAPI

from api.stream_endpoints import router as stream_router

app = FastAPI(title="AnthropicAI MVP v2.0")
app.include_router(stream_router)
