from fastapi import APIRouter, HTTPException
from backend.models import ActionRequest, ActionResult, UndoRequest, UndoResult
from backend.services.action_service import ActionService

router = APIRouter()

action_service = ActionService()


@router.post("/execute", response_model=ActionResult)
async def execute_action(request: ActionRequest):
    try:
        return await action_service.execute_action(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/undo", response_model=UndoResult)
async def undo_action(request: UndoRequest):
    try:
        return await action_service.undo_action(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
