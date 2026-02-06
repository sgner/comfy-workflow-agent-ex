from fastmcp import FastMCP
from typing import Dict, Any, List, Optional
import httpx
import json


mcp = FastMCP("ComfyUI Workflow Agent")


@mcp.tool()
async def search_github_issues(query: str, limit: int = 10) -> str:
    """Search GitHub for ComfyUI related issues and solutions.
    
    Args:
        query: Search query for the issue or error
        limit: Maximum number of results to return
    
    Returns:
        JSON string containing search results
    """
    try:
        from backend.config import settings, get_github_token
        
        headers = {}
        github_token = get_github_token()
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        
        search_query = f"{query} comfyui error issue"
        url = f"https://api.github.com/search/issues"
        params = {
            "q": search_query,
            "per_page": limit,
            "sort": "updated",
            "order": "desc"
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get("items", []):
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("html_url", ""),
                        "body": item.get("body", "")[:500],
                        "state": item.get("state", ""),
                        "comments": item.get("comments", 0)
                    })
                return json.dumps(results, ensure_ascii=False, indent=2)
            else:
                return json.dumps({"error": f"GitHub API returned {response.status_code}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def search_web(query: str) -> str:
    """Search the web for ComfyUI solutions and documentation.
    
    Args:
        query: Search query
    
    Returns:
        JSON string containing search results
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        from backend.config import settings
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            api_key=settings.GOOGLE_API_KEY
        )
        
        prompt = f"""
        Search the web for solutions to this ComfyUI error/problem:
        
        Query: {query}
        
        Return results in JSON format with these fields:
        - title: The title of the page/result
        - url: The URL
        - snippet: A brief description/snippet
        
        Return up to 10 results.
        """
        
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        
        import re
        json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
        if json_match:
            return json_match.group()
        
        return json.dumps([])
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def analyze_workflow(workflow_json: str) -> str:
    """Analyze a ComfyUI workflow and provide insights.
    
    Args:
        workflow_json: JSON string of the workflow
    
    Returns:
        JSON string containing analysis results
    """
    try:
        from backend.tools.workflow_analyzer import WorkflowAnalyzer
        
        analyzer = WorkflowAnalyzer()
        workflow = json.loads(workflow_json)
        
        analysis = await analyzer.analyze_workflow(workflow, "en")
        
        return json.dumps({
            "summary": analysis.summary,
            "data_flow": analysis.data_flow,
            "key_nodes": analysis.key_nodes,
            "issues": [issue.model_dump() for issue in analysis.issues],
            "suggestions": analysis.suggestions
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def detect_workflow_issues(workflow_json: str) -> str:
    """Detect issues in a ComfyUI workflow.
    
    Args:
        workflow_json: JSON string of the workflow
    
    Returns:
        JSON string containing detected issues
    """
    try:
        from backend.tools.workflow_analyzer import WorkflowAnalyzer
        
        analyzer = WorkflowAnalyzer()
        workflow = json.loads(workflow_json)
        
        nodes = workflow.get("nodes", [])
        links = workflow.get("links", [])
        
        issues = await analyzer._detect_issues(nodes, links)
        
        return json.dumps(
            [issue.model_dump() for issue in issues],
            ensure_ascii=False,
            indent=2
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_workflow_data_flow(workflow_json: str) -> str:
    """Get the data flow of a ComfyUI workflow.
    
    Args:
        workflow_json: JSON string of the workflow
    
    Returns:
        JSON string containing data flow information
    """
    try:
        from backend.tools.workflow_analyzer import WorkflowAnalyzer
        
        analyzer = WorkflowAnalyzer()
        workflow = json.loads(workflow_json)
        
        nodes = workflow.get("nodes", [])
        links = workflow.get("links", [])
        
        data_flow = analyzer._analyze_data_flow(nodes, links)
        
        return json.dumps({
            "data_flow": data_flow,
            "total_connections": len(data_flow)
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def execute_workflow_action(
    action_type: str,
    action_data: str,
    session_id: str
) -> str:
    """Execute an action on the workflow.
    
    Args:
        action_type: Type of action (update_config, install_node, modify_workflow, fix_connection, reset_node)
        action_data: JSON string of action data
        session_id: Session identifier
    
    Returns:
        JSON string containing action result
    """
    try:
        from backend.tools.action_tools import ActionTools
        
        action_tools = ActionTools()
        data = json.loads(action_data)
        
        result = await action_tools.execute_action(action_type, data, session_id)
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def undo_workflow_action(action_id: str) -> str:
    """Undo a previously executed workflow action.
    
    Args:
        action_id: ID of the action to undo
    
    Returns:
        JSON string containing undo result
    """
    try:
        from backend.tools.action_tools import ActionTools
        
        action_tools = ActionTools()
        result = await action_tools.undo_action(action_id)
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_action_history(session_id: str) -> str:
    """Get the action history for a session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        JSON string containing action history
    """
    try:
        from backend.action_history import action_history
        
        actions = action_history.get_session_actions(session_id)
        
        return json.dumps(actions, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def parse_error_log(error_log: str) -> str:
    """Parse and analyze a ComfyUI error log.
    
    Args:
        error_log: The error log text
    
    Returns:
        JSON string containing parsed error information
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        from backend.config import settings
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            api_key=settings.GOOGLE_API_KEY
        )
        
        prompt = f"""
        Analyze this ComfyUI error log and extract:
        1. Error type/category
        2. Error message
        3. Node ID (if applicable)
        4. Stack trace key points
        5. Possible causes
        
        Error Log:
        {error_log}
        
        Return in JSON format.
        """
        
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        
        import re
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            return json_match.group()
        
        return json.dumps({"error": "Could not parse error log"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def suggest_fixes(error_log: str, workflow_json: Optional[str] = None) -> str:
    """Suggest fixes for a ComfyUI error.
    
    Args:
        error_log: The error log text
        workflow_json: Optional JSON string of the workflow
    
    Returns:
        JSON string containing suggested fixes
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        from backend.config import settings
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            api_key=settings.GOOGLE_API_KEY
        )
        
        workflow_info = ""
        if workflow_json:
            workflow_info = f"\n\nWorkflow:\n{workflow_json}"
        
        prompt = f"""
        Analyze this ComfyUI error and suggest fixes.
        
        Error Log:
        {error_log}
        {workflow_info}
        
        Return in JSON format with:
        - error_type: Type of error
        - summary: Brief summary
        - solutions: Array of solution objects with:
          - description: Description of the solution
          - steps: Array of steps to implement
          - requires_action: Boolean if it can be auto-fixed
          - action_type: Type of action if auto-fixable
          - action_data: Data needed for the action
        """
        
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        
        import re
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            return json_match.group()
        
        return json.dumps({"error": "Could not generate fixes"})
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
