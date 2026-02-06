from typing import Dict, Any
from backend.models import WorkflowParseRequest, WorkflowParseResponse, WorkflowAnalysis
from backend.tools.workflow_analyzer import WorkflowAnalyzer


class WorkflowService:
    def __init__(self):
        self.analyzer = WorkflowAnalyzer()
    
    async def parse_workflow(self, request: WorkflowParseRequest) -> WorkflowParseResponse:
        workflow_dict = request.workflow.model_dump()
        
        analysis = await self.analyzer.analyze_workflow(
            workflow_dict,
            request.language.value
        )
        
        return WorkflowParseResponse(
            analysis=analysis,
            workflow_json=workflow_dict
        )
    
    async def analyze_workflow(self, request: WorkflowParseRequest) -> Dict[str, Any]:
        workflow_dict = request.workflow.model_dump()
        
        analysis = await self.analyzer.analyze_workflow(
            workflow_dict,
            request.language.value
        )
        
        return {
            "summary": analysis.summary,
            "data_flow": analysis.data_flow,
            "key_nodes": analysis.key_nodes,
            "issues": [issue.model_dump() for issue in analysis.issues],
            "suggestions": analysis.suggestions
        }
