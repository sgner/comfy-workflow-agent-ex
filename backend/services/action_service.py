from typing import Dict, Any
from backend.models import ActionRequest, ActionResult, UndoRequest, UndoResult
from backend.tools.action_tools import ActionTools
from backend.action_history import action_history


class ActionService:
    def __init__(self):
        self.action_tools = ActionTools()
    
    async def execute_action(self, request: ActionRequest) -> ActionResult:
        try:
            result = await self.action_tools.execute_action(
                request.action_type,
                request.action_data,
                request.session_id
            )
            
            return ActionResult(
                success=result.get("success", False),
                message=result.get("message", ""),
                data=result.get("data"),
                can_undo=result.get("can_undo", True),
                undo_action=result.get("action_id")
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Failed to execute action: {str(e)}",
                can_undo=False
            )
    
    async def undo_action(self, request: UndoRequest) -> UndoResult:
        try:
            result = await self.action_tools.undo_action(request.action_id)
            
            return UndoResult(
                success=result.get("success", False),
                message=result.get("message", ""),
                restored_state=result.get("restored_state")
            )
        except Exception as e:
            return UndoResult(
                success=False,
                message=f"Failed to undo action: {str(e)}"
            )
