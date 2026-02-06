import httpx
from typing import List, Dict, Any, Optional
from backend.config import settings, get_github_token


class SearchTools:
    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT
    
    def _get_github_token(self) -> Optional[str]:
        return get_github_token()
    
    async def search_github(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        results = []
        
        try:
            headers = {}
            github_token = self._get_github_token()
            if github_token:
                headers["Authorization"] = f"token {github_token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                search_query = f"{query} comfyui error issue"
                url = f"https://api.github.com/search/issues"
                params = {
                    "q": search_query,
                    "per_page": limit,
                    "sort": "updated",
                    "order": "desc"
                }
                
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("items", []):
                        results.append({
                            "source": "github",
                            "title": item.get("title", ""),
                            "url": item.get("html_url", ""),
                            "body": item.get("body", "")[:500],
                            "state": item.get("state", ""),
                            "comments": item.get("comments", 0),
                            "created_at": item.get("created_at", ""),
                            "updated_at": item.get("updated_at", "")
                        })
        except Exception as e:
            print(f"GitHub search error: {e}")
        
        return results
    
    async def search_web(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        results = []
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage
            
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
            
            Return up to {limit} results.
            """
            
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            
            import re
            import json
            
            json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
            if json_match:
                try:
                    parsed_results = json.loads(json_match.group())
                    for item in parsed_results:
                        results.append({
                            "source": "web",
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("snippet", "")
                        })
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"Web search error: {e}")
        
        return results
    
    async def analyze_solutions(
        self,
        search_results: List[Dict[str, Any]],
        error_log: str,
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        if not search_results:
            return []
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage, SystemMessage
            from backend.config import settings
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                api_key=settings.GOOGLE_API_KEY
            )
            
            language_map = {
                "en": "Analyze these search results and provide solutions in English.",
                "zh": "分析这些搜索结果并用中文提供解决方案。",
                "ja": "これらの検索結果を分析し、日本語で解決策を提供してください。",
                "ko": "이 검색 결과를 분석하고 한국어로 솔루션을 제공하세요."
            }
            
            system_prompt = language_map.get(language, language_map["en"])
            
            results_text = "\n\n".join([
                f"Source: {r['source']}\nTitle: {r['title']}\nURL: {r['url']}\n"
                f"Content: {r.get('body', r.get('snippet', ''))}"
                for r in search_results[:5]
            ])
            
            prompt = f"""
            {system_prompt}
            
            Error Log:
            {error_log}
            
            Search Results:
            {results_text}
            
            Analyze the search results and provide a consolidated solution. 
            Return in JSON format with these fields:
            - description: Brief description of the solution
            - steps: List of steps to fix the issue
            - code_snippet: Any relevant code snippet (optional)
            - requires_action: Boolean - can this be fixed automatically?
            - action_type: Type of action if requires_action is true (e.g., "update_config", "install_node", "modify_workflow")
            - action_data: Data needed for the action (optional)
            """
            
            response = await llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ])
            
            import re
            import json
            
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                try:
                    solution = json.loads(json_match.group())
                    return [solution]
                except json.JSONDecodeError:
                    pass
            
            return [{
                "description": response.content,
                "steps": [],
                "requires_action": False
            }]
        except Exception as e:
            print(f"Solution analysis error: {e}")
            return []
