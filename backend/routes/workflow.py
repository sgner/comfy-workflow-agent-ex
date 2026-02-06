from fastapi import APIRouter, HTTPException
from backend.models import WorkflowParseRequest, WorkflowParseResponse
from backend.services.workflow_service import WorkflowService

router = APIRouter()

workflow_service = WorkflowService()


@router.post("/parse", response_model=WorkflowParseResponse)
async def parse_workflow(request: WorkflowParseRequest):
    try:
        return await workflow_service.parse_workflow(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_workflow(request: WorkflowParseRequest):
    try:
        return await workflow_service.analyze_workflow(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
