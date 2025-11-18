from dataclasses import dataclass

@dataclass
class Prompt:
    id: str
    purpose: str
    name: str
    template: str
    version: int = 1

    def update(self, template: str):
        ...

    def render(self, **kwargs: str):
        ...
