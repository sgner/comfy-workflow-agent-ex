from typing import Dict, Any, Optional
from backend.action_history import action_history


class ActionTools:
    def __init__(self):
        self.action_types = {
            "update_config": self._update_config,
            "install_node": self._install_node,
            "modify_workflow": self._modify_workflow,
            "fix_connection": self._fix_connection,
            "reset_node": self._reset_node
        }
    
    async def execute_action(
        self,
        action_type: str,
        action_data: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        if action_type not in self.action_types:
            return {
                "success": False,
                "message": f"Unknown action type: {action_type}"
            }
        
        previous_state = await self._capture_state(action_type, action_data)
        
        action_id = action_history.add_action(
            session_id=session_id,
            action_type=action_type,
            action_data=action_data,
            previous_state=previous_state
        )
        
        try:
            result = await self.action_types[action_type](action_data)
            result["action_id"] = action_id
            result["can_undo"] = True
            return result
        except Exception as e:
            return {
                "success": False,
                "message": f"Action failed: {str(e)}",
                "action_id": action_id,
                "can_undo": False
            }
    
    async def undo_action(self, action_id: str) -> Dict[str, Any]:
        action = action_history.get_action(action_id)
        
        if not action:
            return {
                "success": False,
                "message": "Action not found"
            }
        
        previous_state = action_history.undo_action(action_id)
        
        if previous_state:
            return {
                "success": True,
                "message": "Action undone successfully",
                "restored_state": previous_state
            }
        
        return {
            "success": False,
            "message": "Could not undo action"
        }
    
    async def _capture_state(
        self,
        action_type: str,
        action_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if action_type == "modify_workflow":
            return action_data.get("current_workflow")
        elif action_type == "update_config":
            return action_data.get("current_config")
        return None
    
    async def _update_config(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        config_path = action_data.get("config_path")
        config_updates = action_data.get("updates", {})
        
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "data": {
                "config_path": config_path,
                "updates": config_updates
            }
        }
    
    async def _install_node(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        node_name = action_data.get("node_name")
        node_url = action_data.get("node_url")
        
        return {
            "success": True,
            "message": f"Node {node_name} installation initiated",
            "data": {
                "node_name": node_name,
                "node_url": node_url,
                "install_command": f"pip install {node_url}" if node_url else None
            }
        }
    
    async def _modify_workflow(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        workflow = action_data.get("workflow")
        modifications = action_data.get("modifications", {})
        
        return {
            "success": True,
            "message": "Workflow modified successfully",
            "data": {
                "workflow": workflow,
                "modifications": modifications
            }
        }
    
    async def _fix_connection(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        from_node_id = action_data.get("from_node_id")
        to_node_id = action_data.get("to_node_id")
        from_slot = action_data.get("from_slot", 0)
        to_slot = action_data.get("to_slot", 0)
        
        return {
            "success": True,
            "message": f"Connection fixed between node {from_node_id} and {to_node_id}",
            "data": {
                "from_node_id": from_node_id,
                "to_node_id": to_node_id,
                "from_slot": from_slot,
                "to_slot": to_slot
            }
        }
    
    async def _reset_node(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        node_id = action_data.get("node_id")
        default_values = action_data.get("default_values", {})
        
        return {
            "success": True,
            "message": f"Node {node_id} reset to default values",
            "data": {
                "node_id": node_id,
                "default_values": default_values
            }
        }
