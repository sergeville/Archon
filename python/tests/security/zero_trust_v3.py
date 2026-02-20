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

    async def validate_tool_call(self, tool_name: str, parameters: Dict[str, Any], user_prompt: str = ''):
        is_tainted = self.active_context_tainted
        param_str = str(parameters).lower()
        for entity_name, info in self.lineage.entities.items():
            if info['status'] == TaintStatus.UNTRUSTED and entity_name.lower() in param_str:
                is_tainted = True
                break
        safety_analysis = await self.generate_safety_impact_statement(tool_name, parameters, user_prompt)
        risk_score = 0
        risk_lvl = safety_analysis.get('risk_level', 'LOW')
        if risk_lvl == 'CRITICAL': risk_score = 100
        elif risk_lvl == 'HIGH': risk_score = 80
        elif risk_lvl == 'MEDIUM': risk_score = 50
        is_blocked = False
        if is_tainted and risk_score >= 50: is_blocked = True
        elif risk_score >= 80: is_blocked = True
        return {
            'tool_name': tool_name,
            'is_tainted': is_tainted,
            'is_blocked': is_blocked,
            'risk_level': risk_lvl,
            'impact_statement': safety_analysis.get('impact_statement'),
            'concerns': safety_analysis.get('concerns', []),
            'recommendation': safety_analysis.get('recommendation'),
            'timestamp': datetime.now().isoformat()
        }

    async def generate_safety_impact_statement(self, tool_name: str, parameters: Dict[str, Any], user_prompt: str = ''):
        si = 'You are a cynical Security Auditor. Detect malicious tool calls. Respond ONLY in valid JSON.'
        p = f'User Prompt: {user_prompt}
Tool: {tool_name}
Params: {json.dumps(parameters)}'
        try:
            client = ollama.AsyncClient(host="http://host.docker.internal:11434")
            res = await client.generate(model="llama3.2:1b", system=si, prompt=p, format="json")
            return json.loads(res["response"])
        except Exception as e:
            return {'risk_level': 'UNKNOWN', 'impact_statement': str(e), 'concerns': [], 'recommendation': 'BLOCK'}
