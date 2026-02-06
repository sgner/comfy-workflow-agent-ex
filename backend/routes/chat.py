
from fastapi import APIRouter, HTTPException
from backend.models import ChatRequest, ChatChunk
from backend.services.chat_service import ChatService

router = APIRouter()

chat_service = ChatService()


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    try:
        return await chat_service.stream_chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message")
async def send_message(request: ChatRequest):
    try:
        print(request)
        response = await chat_service.process_message(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    try:
        return await chat_service.get_history(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
