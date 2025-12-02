from typing import Dict, List, Optional, Any
import json
import os
from datetime import datetime
from pathlib import Path


class PromptVersion:
    def __init__(self, version: str, template: str, variables: List[str], metadata: Dict[str, Any] = None):
        self.version = version
        self.template = template
        self.variables = variables
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.usage_count = 0
        self.success_rate = 0.0
        self.avg_tokens = 0
        
    def format(self, **kwargs) -> str:
        return self.template.format(**kwargs)
    
    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "template": self.template,
            "variables": self.variables,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "avg_tokens": self.avg_tokens
        }


class PromptManager:
    def __init__(self, storage_path: str = "src/music_agent/prompts/prompt_registry.json"):
        self.storage_path = Path(storage_path)
        self.prompts: Dict[str, Dict[str, PromptVersion]] = {}
        self.active_variants: Dict[str, str] = {}
        self.load_prompts()
        
    def register_prompt(self, agent_name: str, version: str, template: str, 
                       variables: List[str], metadata: Dict[str, Any] = None, 
                       set_active: bool = False):
        if agent_name not in self.prompts:
            self.prompts[agent_name] = {}
            
        prompt_version = PromptVersion(version, template, variables, metadata)
        self.prompts[agent_name][version] = prompt_version
        
        if set_active or agent_name not in self.active_variants:
            self.active_variants[agent_name] = version
            
        self.save_prompts()
        
    def get_prompt(self, agent_name: str, version: Optional[str] = None) -> PromptVersion:
        if agent_name not in self.prompts:
            raise ValueError(f"No prompts registered for agent: {agent_name}")
            
        if version is None:
            version = self.active_variants.get(agent_name)
            
        if version not in self.prompts[agent_name]:
            raise ValueError(f"Version {version} not found for agent {agent_name}")
            
        prompt = self.prompts[agent_name][version]
        prompt.usage_count += 1
        return prompt
    
    def set_active_variant(self, agent_name: str, version: str):
        if agent_name not in self.prompts or version not in self.prompts[agent_name]:
            raise ValueError(f"Invalid agent or version: {agent_name}/{version}")
        self.active_variants[agent_name] = version
        self.save_prompts()
        
    def get_all_variants(self, agent_name: str) -> Dict[str, PromptVersion]:
        return self.prompts.get(agent_name, {})
    
    def track_success(self, agent_name: str, version: str, success: bool, tokens: int = 0):
        if agent_name in self.prompts and version in self.prompts[agent_name]:
            prompt = self.prompts[agent_name][version]
            old_count = prompt.usage_count
            prompt.success_rate = (prompt.success_rate * old_count + (1 if success else 0)) / (old_count + 1)
            prompt.avg_tokens = (prompt.avg_tokens * old_count + tokens) / (old_count + 1)
            self.save_prompts()
    
    def get_metrics(self, agent_name: str) -> Dict[str, Any]:
        if agent_name not in self.prompts:
            return {}
            
        metrics = {}
        for version, prompt in self.prompts[agent_name].items():
            metrics[version] = {
                "usage_count": prompt.usage_count,
                "success_rate": prompt.success_rate,
                "avg_tokens": prompt.avg_tokens,
                "metadata": prompt.metadata,
                "is_active": self.active_variants.get(agent_name) == version
            }
        return metrics
    
    def compare_variants(self, agent_name: str) -> List[Dict[str, Any]]:
        metrics = self.get_metrics(agent_name)
        return sorted(
            [{"version": v, **m} for v, m in metrics.items()],
            key=lambda x: (x["success_rate"], -x["avg_tokens"]),
            reverse=True
        )
    
    def save_prompts(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "active_variants": self.active_variants,
            "prompts": {
                agent: {ver: p.to_dict() for ver, p in versions.items()}
                for agent, versions in self.prompts.items()
            }
        }
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def load_prompts(self):
        if not self.storage_path.exists():
            return
            
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.active_variants = data.get("active_variants", {})
            
            for agent_name, versions in data.get("prompts", {}).items():
                self.prompts[agent_name] = {}
                for version, prompt_data in versions.items():
                    prompt = PromptVersion(
                        prompt_data["version"],
                        prompt_data["template"],
                        prompt_data["variables"],
                        prompt_data.get("metadata", {})
                    )
                    prompt.created_at = prompt_data.get("created_at", datetime.now().isoformat())
                    prompt.usage_count = prompt_data.get("usage_count", 0)
                    prompt.success_rate = prompt_data.get("success_rate", 0.0)
                    prompt.avg_tokens = prompt_data.get("avg_tokens", 0)
                    self.prompts[agent_name][version] = prompt
        except Exception as e:
            pass


_global_manager = None

def get_prompt_manager() -> PromptManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = PromptManager()
    return _global_manager
