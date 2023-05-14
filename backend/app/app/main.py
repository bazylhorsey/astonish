from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from app.core.config import settings
from app.api.v1.api import api_router as api_router_v1


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

@app.get("/")
async def root():
    """
    An example "Hello world" FastAPI route.
    """
    # if oso.is_allowed(user, "read", message):
    return {"message": "Hello World"}

@app.get("/.well-known/ai-plugin.json", response_class=FileResponse)
async def get_plugin_manifest() -> FileResponse:
    return FileResponse("app/.well-known/ai-plugin.json")

app.include_router(api_router_v1, prefix=settings.API_V1_STR)