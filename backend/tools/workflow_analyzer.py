
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable
from backend.models import ComfyWorkflow, ComfyNode, WorkflowIssue, WorkflowAnalysis
import json
import re

class WorkflowAnalyzer:
    def __init__(self):
        self.node_categories = {
            "loaders": ["LoadImage", "LoadCheckpoint", "LoadText", "LoadAudio", "LoadVideo"],
            "samplers": ["KSampler", "KSamplerAdvanced"],
            "encoders": ["VAEEncode", "CLIPTextEncode"],
            "decoders": ["VAEDecode"],
            "conditioning": ["ConditioningCombine", "ConditioningSetArea"],
            "latent": ["LatentUpscale", "LatentComposite", "EmptyLatentImage"],
            "image": ["ImageScale", "ImageUpscale", "ImageComposite", "ImageCrop"],
            "outputs": ["SaveImage", "PreviewImage", "SaveAnimatedWEBP"]
        }

    async def analyze_workflow(
            self,
            workflow: Dict[str, Any],
            language: str = "en"
    ) -> WorkflowAnalysis:
        # Fallback to deterministic if no LLM callback is provided (for legacy support or quick checks)
        # Note: This method is kept for compatibility but the agent should prefer analyze_workflow_with_llm
        nodes = workflow.get("nodes", [])
        links = workflow.get("links", [])

        issues = await self._detect_issues(nodes, links)
        data_flow = self._analyze_data_flow(nodes, links)
        key_nodes = self._identify_key_nodes(nodes)
        summary = self._generate_summary(nodes, data_flow, key_nodes, language)
        suggestions = self._generate_suggestions(issues, nodes, language)

        return WorkflowAnalysis(
            summary=summary,
            data_flow=data_flow,
            key_nodes=key_nodes,
            issues=issues,
            suggestions=suggestions
        )

    async def analyze_workflow_with_llm(
        self, 
        workflow: Dict[str, Any], 
        llm_call_func: Callable[[str], Awaitable[str]], 
        language: str = "en"
    ) -> WorkflowAnalysis:
        """
        Uses an LLM to analyze the workflow, ensuring better understanding of connections and logic.
        """
        # 1. Simplify workflow to save tokens but keep essential structure
        
        # Helper: Convert links back to array format if they are dicts (from Pydantic)
        # Structure: [id, origin_id, origin_slot, target_id, target_slot, type]
        links_for_prompt = []
        for l in workflow.get("links", []):
            if isinstance(l, list):
                links_for_prompt.append(l)
            elif isinstance(l, dict):
                links_for_prompt.append([
                    l.get("id"),
                    l.get("origin_id"),
                    l.get("origin_slot"),
                    l.get("target_id"),
                    l.get("target_slot"),
                    l.get("type")
                ])

        simplified = {
            "nodes": [
                {
                    "id": n.get("id"),
                    "type": n.get("type"),
                    "inputs": [{"name": i.get("name"), "link_id": i.get("link")} for i in n.get("inputs", [])],
                    "outputs": [{"name": o.get("name"), "has_links": bool(o.get("links"))} for o in n.get("outputs", [])],
                    "widgets": n.get("widgets_values")
                } for n in workflow.get("nodes", [])
            ],
            "links": links_for_prompt 
        }
        
        prompt = f"""
        You are an expert ComfyUI workflow analyzer. 
        Your task is to analyze the provided workflow JSON and return a structured analysis in JSON format.

        [WORKFLOW STRUCTURE EXPLANATION]
        - Nodes have ID, Type, Inputs, and Outputs.
        - Links array format: [link_id, origin_node_id, origin_slot_index, target_node_id, target_slot_index, type].
        - A connection exists if a link entry connects an Origin Node to a Target Node.
        
        [TASK]
        1. **Summary**: Briefly describe what this workflow does based on the nodes and connections.
        2. **Data Flow**: List the high-level flow of data (e.g., LoadImage -> KSampler -> SaveImage). Trace the links array to find actual connections.
        3. **Key Nodes**: Identify the most important nodes (CheckpointLoader, KSampler, SaveImage, etc.).
        4. **Issues**: specific errors.
           - Check for nodes with missing inputs (where 'link_id' is null).
           - Check for broken flows (e.g., KSampler not connected to VAE Decode).
           - Count the links correctly based on the 'links' array.
        5. **Suggestions**: actionable advice to improve or fix the workflow.

        [OUTPUT FORMAT]
        Return ONLY valid JSON with this schema:
        {{
            "summary": "string",
            "data_flow": ["string", "string"],
            "key_nodes": [{{"id": "string", "type": "string", "description": "string"}}],
            "issues": [
                {{"id": "unique_id", "node_id": int, "severity": "error|warning", "message": "string", "fix_suggestion": "string"}}
            ],
            "suggestions": ["string"]
        }}

        [WORKFLOW JSON]
        {json.dumps(simplified)}
        
        Analyze in {language} language.
        """
        
        try:
            response_text = await llm_call_func(prompt)
            # Extract JSON from markdown code block if present
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                response_text = json_match.group(1)
            else:
                # Fallback: try to find the first { and last }
                json_match = re.search(r'(\{[\s\S]*\})', response_text)
                if json_match:
                    response_text = json_match.group(1)
            
            data = json.loads(response_text)
            
            # Convert to internal model
            issues = [WorkflowIssue(**i) for i in data.get("issues", [])]
            
            return WorkflowAnalysis(
                summary=data.get("summary", "Analysis failed"),
                data_flow=data.get("data_flow", []),
                key_nodes=data.get("key_nodes", []),
                issues=issues,
                suggestions=data.get("suggestions", [])
            )
        except Exception as e:
            print(f"LLM Analysis failed: {e}")
            # Fallback to deterministic method
            return await self.analyze_workflow(workflow, language)

    async def _detect_issues(
            self,
            nodes: List[Dict[str, Any]],
            links: List[Any]  # Changed type hint to Any to cover both List and Dict
    ) -> List[WorkflowIssue]:
        issues = []
        for link in links:
            pass

        for node in nodes:
            node_id = node.get("id")
            inputs = node.get("inputs", [])

            for idx, input_data in enumerate(inputs):
                # input_data.get("link") 返回的是 link_id (int) 或 None
                if input_data.get("link") is None:
                    input_name = input_data.get("name", "")
                    # 忽略一些可选或默认参数
                    if input_name not in ["seed", "width", "height", "batch_size", "clip"]:
                        issues.append(WorkflowIssue(
                            id=f"missing_input_{node_id}_{idx}",
                            node_id=str(node_id),
                            severity="warning",
                            message=f"Node {node.get('type')} has missing input: {input_name}",
                            fix_suggestion=f"Connect a node to the {input_name} input or provide a value"
                        ))

        node_types = [node.get("type") for node in nodes]
        if "KSampler" in node_types and "VAEDecode" not in node_types:
            issues.append(WorkflowIssue(
                id="missing_vae_decode",
                node_id=None,
                severity="warning",
                message="Workflow has KSampler but no VAE Decode node",
                fix_suggestion="Add a VAE Decode node to convert latent images to visible images"
            ))

        if "KSampler" in node_types and "SaveImage" not in node_types and "PreviewImage" not in node_types:
            issues.append(WorkflowIssue(
                id="missing_output",
                node_id=None,
                severity="info",
                message="Workflow has no output node (SaveImage or PreviewImage)",
                fix_suggestion="Add a SaveImage or PreviewImage node to see the results"
            ))

        return issues

    def _analyze_data_flow(
            self,
            nodes: List[Dict[str, Any]],
            links: List[Any]
    ) -> List[str]:
        data_flow = []

        link_map = {}

        # --- 【修复重点】兼容 List 和 Dict 两种格式的 Link ---
        for link in links:
            l_id, origin_id, origin_slot, target_id, target_slot = None, None, None, None, None

            if isinstance(link, list) and len(link) >= 5:
                # ComfyUI 标准数组格式: [id, origin_id, origin_slot, target_id, target_slot, type]
                l_id = link[0]
                origin_id = link[1]
                origin_slot = link[2]
                target_id = link[3]
                target_slot = link[4]
            elif isinstance(link, dict):
                # Pydantic dump 后的字典格式
                l_id = link.get("id")
                origin_id = link.get("origin_id")
                origin_slot = link.get("origin_slot")
                target_id = link.get("target_id")
                target_slot = link.get("target_slot")

            # 只有当解析成功且有关联ID时才存入 map
            if l_id is not None and target_id is not None:
                # 强转为 str 以确保 map 查找时类型一致
                link_map[str(l_id)] = {
                    "origin_id": origin_id,
                    "origin_slot": origin_slot,
                    "target_id": target_id,
                    "target_slot": target_slot
                }
        # ----------------------------------------------------

        # 创建 ID 到 Node 的映射，注意 ID 可能是 int 或 str，统一转 str 处理或者保持原样
        # 这里为了稳妥，查找时做类型兼容
        node_dict = {str(node["id"]): node for node in nodes}

        for node in nodes:
            node_type = node.get("type", "Unknown")
            node_id = node.get("id")

            outputs = node.get("outputs", [])
            for output in outputs:
                # 检查 outputs 里的 links
                node_links = output.get("links")
                if node_links:
                    for link_id in node_links:
                        # 转换 link_id 为 str 进行查找
                        str_link_id = str(link_id)
                        if str_link_id in link_map:
                            target_id = link_map[str_link_id]["target_id"]
                            # 尝试获取 target node
                            target_node = node_dict.get(str(target_id))

                            if target_node:
                                data_flow.append(
                                    f"{node_type} (Node {node_id}) -> {target_node.get('type', 'Unknown')} (Node {target_id})"
                                )

        return data_flow[:10]

    def _identify_key_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        key_nodes = []

        for node in nodes:
            node_type = node.get("type", "")
            node_id = node.get("id")

            # 简单的辅助函数来检查分类
            def check_category(category_key, category_name, desc):
                if any(cat_type in node_type for cat_type in self.node_categories[category_key]):
                    key_nodes.append({
                        "id": str(node_id),  # 统一 ID 为字符串
                        "type": node_type,
                        "category": category_name,
                        "description": desc
                    })
                    return True
                return False

            if check_category("loaders", "loader", "Loads input data (images, models, etc.)"): continue
            if check_category("samplers", "sampler", "Generates images using the diffusion model"): continue
            if check_category("outputs", "output", "Saves or previews the generated images"): continue

        return key_nodes

    def _generate_summary(
            self,
            nodes: List[Dict[str, Any]],
            data_flow: List[str],
            key_nodes: List[Dict[str, Any]],
            language: str = "en"
    ) -> str:
        node_count = len(nodes)

        summaries = {
            "en": f"This workflow contains {node_count} nodes. "
                  f"Key components include {len(key_nodes)} important nodes. "
                  f"The workflow processes data through {len(data_flow)} connections.",
            "zh": f"此工作流包含 {node_count} 个节点。"
                  f"关键组件包括 {len(key_nodes)} 个重要节点。"
                  f"工作流通过 {len(data_flow)} 个连接处理数据。",
            "ja": f"このワークフローには {node_count} 個のノードが含まれています。"
                  f"主要コンポーネントには {len(key_nodes)} 個の重要なノードがあります。",
            "ko": f"이 워크플로우에는 {node_count} 개의 노드가 포함되어 있습니다."
                  f"주요 구성 요소에는 {len(key_nodes)} 개의 중요한 노드가 있습니다."
        }

        return summaries.get(language, summaries["en"])

    def _generate_suggestions(
            self,
            issues: List[WorkflowIssue],
            nodes: List[Dict[str, Any]],
            language: str = "en"
    ) -> List[str]:
        suggestions = []

        suggestions_map = {
            "en": [
                "Review the workflow connections for any missing links",
                "Consider adding a preview node to see intermediate results",
                "Check if all required custom nodes are installed"
            ],
            "zh": [
                "检查工作流连接是否有缺失的链接",
                "考虑添加预览节点以查看中间结果",
                "检查是否已安装所有必需的自定义节点"
            ],
            "ja": [
                "欠けているリンクがないかワークフロー接続を確認してください",
                "中間結果を確認するためにプレビューノードを追加することを検討してください",
                "必要なカスタムノードがすべてインストールされているか確認してください"
            ],
            "ko": [
                "누락된 연결이 없는지 워크플로우 연결을 검토하세요",
                "중간 결과를 보기 위해 미리보기 노드를 추가하는 것을 고려하세요",
                "필요한 사용자 정의 노드가 모두 설치되어 있는지 확인하세요"
            ]
        }

        base_suggestions = suggestions_map.get(language, suggestions_map["en"])

        if issues:
            error_count = len([i for i in issues if i.severity == "error"])
            warning_count = len([i for i in issues if i.severity == "warning"])

            if error_count > 0 or warning_count > 0:
                prefix = {
                    "en": "Fix", "zh": "修复", "ja": "修正", "ko": "수정"
                }.get(language, "Fix")
                msg = {
                    "en": f"{error_count} error(s) and {warning_count} warning(s)",
                    "zh": f"{error_count} 个错误和 {warning_count} 个警告",
                    "ja": f"{error_count} 个のエラーと {warning_count} 个の警告",
                    "ko": f"{error_count} 개의 오류와 {warning_count} 개의 경고"
                }.get(language, f"{error_count} errors")

                suggestions.insert(0, f"{prefix} {msg}")

        return base_suggestions
