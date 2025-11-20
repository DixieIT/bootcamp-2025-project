from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel

class Prompt(BaseModel):

    id: str
    purpose: str
    name: str
    template: str
    version: int = 1
    user_id: str



    def update(self, template: str):
        
        self.template = template
        self.version += 1

    def render(self, **kwargs: str):
        return self.template.format(**kwargs)
