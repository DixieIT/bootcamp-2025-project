from abc import ABC, abstractmethod
from uuid import uuid4
from typing import TypeAlias
import json, os
from typing import Optional
from ..models.domain import Prompt


UserId: TypeAlias = str
PromptId: TypeAlias = str
Purpose: TypeAlias = str

class PromptStore(ABC):

    @abstractmethod
    def create(
            self,
            purpose: Purpose,
            name: str,
            template: Optional[str],
        ) -> Prompt:
        ...

    @abstractmethod
    def list(
            self,
            purpose: Purpose | None = None,
        ) -> list[Prompt]:
        ...

    @abstractmethod
    def get(
            self,
            prompt_id: PromptId,
        ) -> Prompt | None:
        ...

    @abstractmethod
    def patch(
            self,
            prompt_id: PromptId,
            template: Optional[str],
        ) -> Prompt | None:
        ...

    @abstractmethod
    def set_active(
            self,
            user_id: UserId,
            purpose: Purpose,
            prompt_id: PromptId,
        ) -> Prompt | None:
        ...

    @abstractmethod
    def get_active(
            self,
            user_id: UserId,
            purpose: Purpose,
        ) -> Prompt | None:
        ...

    @abstractmethod
    def delete(
            self,
            prompt_id: PromptId,
            user_id: UserId,
        ) -> bool:
        ...


class InMemoryStore(PromptStore):
    """In-memory implementation of PromptStore."""
    def __init__(self) -> None:
        self.prompts: dict[PromptId, Prompt] = {}
        self.active_prompts: dict[tuple[UserId, Purpose], PromptId] = {}

    def create(self, purpose: Purpose, name: str, template: str, user_id: str) -> Prompt:
        prompt_id = str(uuid4())
        print(prompt_id)
        prompt = Prompt(
            id=prompt_id,
            purpose=purpose,
            name=name,
            template=template,
            user_id=user_id
        )
        self.prompts[prompt_id] = prompt
        return prompt

    def list(
            self,
            purpose: Purpose | None = None,
        ) -> list[Prompt]:
        if purpose is None:
            return list(self.prompts.values())
        return [p for p in self.prompts.values() if p.purpose == purpose]

    def get(
            self,
            prompt_id: PromptId,
        ) -> Prompt | None:
        return self.prompts.get(prompt_id)

    def patch(
            self,
            prompt_id: PromptId,
            template: str, user_id
        ) -> Prompt | None:
        prompt = self.prompts.get(prompt_id)

        if prompt is None:
            return None
        
        if user_id != prompt.user_id:
            return None

        prompt.template = template
        return prompt

    def set_active(
            self,
            user_id: UserId,
            purpose: Purpose,
            prompt_id: PromptId,
        ) -> Prompt | None:
        prompt = self.get(prompt_id)
        if prompt is None:
            return None
        self.active_prompts[(user_id, purpose)] = prompt_id
        return prompt

    def get_active(
            self,
            user_id: UserId,
            purpose: Purpose,
        ) -> Prompt | None:
        prompt_id = self.active_prompts.get((user_id, purpose))
        if prompt_id is None:
            return None
        return self.prompts.get(prompt_id)

    def delete(
            self,
            prompt_id: PromptId,
            user_id: UserId,
        ) -> bool:
        prompt = self.prompts.get(prompt_id)
        if prompt is None:
            return False
        if prompt.user_id != user_id:
            return False
        # Remove from active_prompts if it was active
        keys_to_remove = [k for k, v in self.active_prompts.items() if v == prompt_id]
        for key in keys_to_remove:
            del self.active_prompts[key]
        del self.prompts[prompt_id]
        return True


class FileSnapshotStore(InMemoryStore):
    """Wraps InMemoryStore and snapshots to var/data.json on writes."""
    def __init__(self, filepath: str = "var/data.json") -> None:
        super().__init__()
        self.filepath = filepath
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.filepath):
            return
        with open(self.filepath, "r") as f:
            data = json.load(f)
        for p_data in data.get("prompts", []):
            prompt = Prompt.model_validate(p_data)
            self.prompts[prompt.id] = prompt
        for key, prompt_id in data.get("active_prompts", {}).items():
            user_id, purpose = key.split("|", 1)
            self.active_prompts[(user_id, purpose)] = prompt_id



    def _snapshot(self) -> None:
        data = {
            "prompts": [p.model_dump() for p in self.prompts.values()],
            "active_prompts": {
                f"{user_id}|{purpose}": prompt_id
                for (user_id, purpose), prompt_id in self.active_prompts.items()
            },
        }
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=2)

    def create(
            self,
            purpose: Purpose,
            name: str,
            template: str,
            user_id: str
        ) -> Prompt:
        prompt = super().create(purpose, name, template, user_id)
        self._snapshot()
        return prompt

    def patch(
            self,
            prompt_id: PromptId,
            template: str,
            user_id: UserId,
        ) -> Prompt | None:
        prompt = super().patch(prompt_id, template, user_id)
        if prompt is not None:
            self._snapshot()
        return prompt

    def set_active(
            self,
            user_id: UserId,
            purpose: Purpose,
            prompt_id: PromptId,
        ) -> Prompt | None:
        prompt = super().set_active(user_id, purpose, prompt_id)
        if prompt is not None:
            self._snapshot()
        return prompt

    def delete(
            self,
            prompt_id: PromptId,
            user_id: UserId,
        ) -> bool:
        result = super().delete(prompt_id, user_id)
        if result:
            self._snapshot()
        return result