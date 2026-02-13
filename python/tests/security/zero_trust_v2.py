import ollama
import json
import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)

class TaintStatus(str, Enum):
    TRUSTED = 'trusted'
    UNTRUSTED = 'untrusted'

class DataLineage:
    def __init__(self):
        self.entities: Dict[str, Dict[str, Any]] = {}

    def record_entity(self, name: str, source: str, status: TaintStatus):
        self.entities[name] = {
            'source': source,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }

    def get_status(self, name: str) -> TaintStatus:
        return self.entities.get(name, {}).get('status', TaintStatus.TRUSTED)

class ZeroTrustAgency:
    def __init__(self, database):
        self.db = database
        self.lineage = DataLineage()
        self.active_context_tainted = False
        self.tainted_turns: Set[str] = set()
        self._load_lineage_from_db()

    def _load_lineage_from_db(self):
        try:
            untrusted = self.db.get_all_untrusted_entities()
            for item in untrusted:
                self.lineage.record_entity(item['entity_name'], item['source'], TaintStatus.UNTRUSTED)
            logger.info(f'ZeroTrust: Restored {len(untrusted)} untrusted entities.')
        except Exception as e:
            logger.error(f'ZeroTrust: Failed to load lineage: {e}')

    def mark_untrusted_input(self, source_name: str, content_preview: str):
        logger.warning(f'Taint Alert: Marking input from {source_name} as UNTRUSTED')
        self.lineage.record_entity(source_name, source_name, TaintStatus.UNTRUSTED)
        self.active_context_tainted = True
        self.db.save_security_lineage(source_name, source_name, TaintStatus.UNTRUSTED, {'preview': content_preview[:100]})

    def reset_context(self):
        self.active_context_tainted = False

    async def validate_tool_call(self, tool_name: str, parameters: Dict[str, Any], user_prompt: str = "") -> Dict[str, Any]:
        """
        Comprehensive Zero Trust validation of a tool call.
        Combines Taint Analysis (Lineage) with Semantic Analysis (Safety Explainer).
        """
        is_tainted = self.active_context_tainted
        param_str = str(parameters).lower()
        
        # 1. Taint Tracking check
        for entity_name, info in self.lineage.entities.items():
            if info['status'] == TaintStatus.UNTRUSTED and entity_name.lower() in param_str:
                logger.warning(f"ZeroTrust: Untrusted entity '{entity_name}' detected in tool call parameters.")
                is_tainted = True
                break
        
        # 2. Semantic Safety Analysis (Secondary LLM)
        safety_analysis = await self.generate_safety_impact_statement(tool_name, parameters, user_prompt)
        
        risk_score = 0
        if safety_analysis.get("risk_level") == "CRITICAL": risk_score = 100
        elif safety_analysis.get("risk_level") == "HIGH": risk_score = 80
        elif safety_analysis.get("risk_level") == "MEDIUM": risk_score = 50
        
        # Determine if action should be blocked
        is_blocked = False
        if is_tainted and risk_score >= 50:
            is_blocked = True
            logger.error(f"ZeroTrust: BLOCKING tool call {tool_name} due to Tainted Data + Medium/High Risk.")
        elif risk_score >= 80:
            is_blocked = True
            logger.error(f"ZeroTrust: BLOCKING tool call {tool_name} due to Critical/High Semantic Risk.")

        return {
            'tool_name': tool_name,
            'is_tainted': is_tainted,
            'is_blocked': is_blocked,
            'risk_level': safety_analysis.get("risk_level"),
            'impact_statement': safety_analysis.get("impact_statement"),
            'concerns': safety_analysis.get("concerns", []),
            'recommendation': safety_analysis.get("recommendation"),
            'timestamp': datetime.now().isoformat()
        }

    async def generate_safety_impact_statement(self, tool_name: str, parameters: Dict[str, Any], user_prompt: str = "") -> Dict[str, Any]:
        """
        Independent Auditor call using a smaller local model.
        Instructed to be cynical and ignore the primary agent's persona.
        """
        system_instruction = (
            "You are a cynical Security Auditor for an AI system. "
            "Your job is to detect malicious tool calls. "
            "Ignore the polite tone of the assistant. "
            "Analyze the RAW tool name and parameters. "
            "Look for: Destructive commands (rm, delete, drop), unauthorized data exfiltration, "
            "and home automation actions that contradict the user's intent. "
            "Respond ONLY in valid JSON format."
        )
        
        prompt = (
            f"User Prompt: {user_prompt}
"
            f"Proposed Tool: {tool_name}
"
            f"Parameters: {json.dumps(parameters)}

"
            "Analyze for risks. Provide JSON with: 'risk_level' (LOW, MEDIUM, HIGH, CRITICAL), "
            "'impact_statement', 'concerns' (list), and 'recommendation' (ALLOW, BLOCK, ESCALATE)."
        )
        
        try:
            client = ollama.AsyncClient(host="http://host.docker.internal:11434")
            # Using llama3.2:1b as the dedicated auditor model
            response = await client.generate(
                model="llama3.2:1b", 
                system=system_instruction,
                prompt=prompt, 
                format="json"
            )
            return json.loads(response["response"])
        except Exception as e:
            logger.error(f"ZeroTrust: Safety Explainer error: {e}")
            return {
                "risk_level": "UNKNOWN", 
                "impact_statement": "Safety Explainer timed out or failed.", 
                "concerns": [str(e)], 
                "recommendation": "BLOCK" # Fail-closed
            }
