from abc import ABC, abstractmethod
from uuid import uuid4
from typing import TypeAlias
import json, os

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
            template: str,
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
            template: str,
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


class InMemoryStore(PromptStore):
    """In-memory store that holds prompts and active-prompt mappings."""

    _prompts: dict[PromptId, Prompt]
    _active: dict[tuple[UserId, Purpose], PromptId]

    def __init__(self):
        self._prompts = {}
        self._active = {}

    def create(
        self,
        purpose: Purpose,
        name: str,
        template: str,
    ) -> Prompt:
        prompt_id = str(uuid4())
        prompt = Prompt(
            id=prompt_id,
            purpose=purpose,
            name=name,
            template=template,
            version=1,
            is_active=False,
        )
        self._prompts[prompt_id] = prompt
        return prompt

    def list(
        self,
        purpose: Purpose | None = None,
    ) -> list[Prompt]:
        if purpose:
            return [p for p in self._prompts.values() if p.purpose == purpose]
        return list(self._prompts.values())

    def get(
        self,
        prompt_id: PromptId,
    ) -> Prompt | None:
        return self._prompts.get(prompt_id)

    def patch(
        self,
        prompt_id: PromptId,
        template: str,
    ) -> Prompt | None:
        prompt = self.get(prompt_id)
        if prompt:
            prompt.template = template
            prompt.version += 1
        return prompt

    def set_active(
        self,
        user_id: UserId,
        purpose: Purpose,
        prompt_id: PromptId,
    ) -> Prompt | None:
        prompt = self.get(prompt_id)
        if not prompt or prompt.purpose != purpose:
            return None

        self._active[(user_id, purpose)] = prompt_id
        # Note: is_active is a view-model concern, not a core domain attribute.
        # This implementation detail should be handled at the API/schema layer.
        return prompt

    def get_active(
        self,
        user_id: UserId,
        purpose: Purpose,
    ) -> Prompt | None:
        prompt_id = self._active.get((user_id, purpose))
        return self.get(prompt_id) if prompt_id else None


class FileSnapshotStore(InMemoryStore):
    """Wraps InMemoryStore and snapshots to a JSON file on writes."""

    def __init__(self, snapshot_file: str):
        super().__init__()
        self._snapshot_file = snapshot_file
        self._load_snapshot()

    def _load_snapshot(self):
        if not os.path.exists(self._snapshot_file):
            return
        with open(self._snapshot_file, "r") as f:
            data = json.load(f)
            self._prompts = {
                k: Prompt(**v) for k, v in data.get("prompts", {}).items()
            }
            # The values in _active are tuples, but JSON saves them as lists.
            # We need to convert them back to tuples.
            self._active = {
                tuple(k.split(":")): v
                for k, v in data.get("active", {}).items()
            }


    def _save_snapshot(self):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self._snapshot_file), exist_ok=True)
        with open(self._snapshot_file, "w") as f:
            # We need to convert the tuple keys in _active to strings to be able to save them as JSON.
            # We will join the tuple elements with a colon.
            active_for_json = {
                f"{k[0]}:{k[1]}": v for k, v in self._active.items()
            }
            json.dump(
                {
                    "prompts": {k: v.dict() for k, v in self._prompts.items()},
                    "active": active_for_json,
                },
                f,
                indent=2,
            )

    def create(
        self,
        purpose: Purpose,
        name: str,
        template: str,
    ) -> Prompt:
        prompt = super().create(purpose, name, template)
        self._save_snapshot()
        return prompt

    def patch(
        self,
        prompt_id: PromptId,
        template: str,
    ) -> Prompt | None:
        prompt = super().patch(prompt_id, template)
        if prompt:
            self._save_snapshot()
        return prompt

    def set_active(
        self,
        user_id: UserId,
        purpose: Purpose,
        prompt_id: PromptId,
    ) -> Prompt | None:
        prompt = super().set_active(user_id, purpose, prompt_id)
        if prompt:
            self._save_snapshot()
        return prompt