from fastapi.responses import FileResponse
from app.core.config import settings
from app.api.v1.api import api_router as api_router_v1
from uuid import UUID, uuid4
from fastapi_limiter.depends import RateLimiter, WebSocketRateLimiter
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from app.api.deps import get_redis_client
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

@app.websocket("/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: UUID):    
    session_id = str(uuid4())
    key: str = f'user_id:{user_id}:session:{session_id}'    
    await websocket.accept()
    redis_client = await get_redis_client()
    ws_ratelimit = WebSocketRateLimiter(times=200, hours=24)
    chat = ChatOpenAI(temperature=0, openai_api_key=settings.OPENAI_API_KEY)
    chat_history = []
    
    async with db():
        user = await crud.user.get_by_id_active(id=user_id)
        if user != None:            
            await redis_client.set(key, str(websocket))
    
    
    active_connection = await redis_client.get(key)
    if active_connection is None:
        await websocket.send_text(f"Error: User ID '{user_id}' not found or inactive.")
        await websocket.close()
    else:
        while True:
            try:
                # Receive and send back the client message
                data = await websocket.receive_json()
                await ws_ratelimit(websocket)
                user_message = IUserMessage.parse_obj(data)
                user_message.user_id = user_id

                resp = IChatResponse(
                    sender="you",
                    message=user_message.message,
                    type="stream",
                    message_id=str(uuid7()),
                    id=str(uuid7()),
                )
                await websocket.send_json(resp.dict())

                # # Construct a response
                start_resp = IChatResponse(
                    sender="bot", message="", type="start", message_id="", id=""
                )
                await websocket.send_json(start_resp.dict())

                result = chat([HumanMessage(content=resp.message)])                
                chat_history.append((user_message.message, result.content))
                
                
                end_resp = IChatResponse(
                    sender="bot",
                    message=result.content,
                    type="end",
                    message_id=str(uuid7()),
                    id=str(uuid7()),
                )
                await websocket.send_json(end_resp.dict())
            except WebSocketDisconnect:
                logging.info("websocket disconnect")
                break
            except Exception as e:
                logging.error(e)
                resp = IChatResponse(
                    message_id="",
                    id="",
                    sender="bot",
                    message="Sorry, something went wrong. Your user limit of api usages has been reached.",
                    type="error",
                )
                await websocket.send_json(resp.dict())
        
        # Remove the live connection from Redis
        await redis_client.delete(key)

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

