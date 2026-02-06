from typing import Dict, Any, Optional
from datetime import datetime
import uuid


class ActionHistory:
    def __init__(self):
        self.actions: Dict[str, Dict[str, Any]] = {}
    
    def add_action(
        self,
        session_id: str,
        action_type: str,
        action_data: Dict[str, Any],
        previous_state: Optional[Dict[str, Any]] = None
    ) -> str:
        action_id = str(uuid.uuid4())
        self.actions[action_id] = {
            "action_id": action_id,
            "session_id": session_id,
            "action_type": action_type,
            "action_data": action_data,
            "previous_state": previous_state,
            "timestamp": datetime.now().isoformat()
        }
        return action_id
    
    def get_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        return self.actions.get(action_id)
    
    def undo_action(self, action_id: str) -> Optional[Dict[str, Any]]:
        action = self.actions.get(action_id)
        if action:
            return action.get("previous_state")
        return None
    
    def get_session_actions(self, session_id: str) -> list[Dict[str, Any]]:
        return [
            action for action in self.actions.values()
            if action["session_id"] == session_id
        ]


action_history = ActionHistory()
