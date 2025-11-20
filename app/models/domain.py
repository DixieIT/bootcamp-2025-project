from dataclasses import dataclass
from typing import Optional

@dataclass
class Prompt:
    id: str
    purpose: str
    name: str
    template: str
    user_id: str
    version: int = 1

    def update(self, template: str):
        
        self.template = template
        self.version += 1

    def render(self, **kwargs: str):
        return self.template.format(**kwargs)
