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


class DatabaseStore(PromptStore):
    """SQLite-backed implementation of PromptStore."""

    def __init__(self, db_path: str = "var/database.db") -> None:
        import sqlite3
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_tables()

    def _get_conn(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prompts (
                    id TEXT PRIMARY KEY,
                    purpose TEXT NOT NULL,
                    name TEXT NOT NULL,
                    template TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    user_id TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_prompts (
                    user_id TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    activated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, purpose),
                    FOREIGN KEY (prompt_id) REFERENCES prompts(id)
                )
            ''')
            conn.commit()

    def _row_to_prompt(self, row) -> Prompt:
        return Prompt(
            id=row["id"],
            purpose=row["purpose"],
            name=row["name"],
            template=row["template"],
            version=row["version"],
            user_id=row["user_id"],
        )

    def create(self, purpose: Purpose, name: str, template: str, user_id: str) -> Prompt:
        prompt_id = str(uuid4())
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO prompts (id, purpose, name, template, version, user_id)
                VALUES (?, ?, ?, ?, 1, ?)
            ''', (prompt_id, purpose, name, template, user_id))
            conn.commit()
        return Prompt(
            id=prompt_id,
            purpose=purpose,
            name=name,
            template=template,
            version=1,
            user_id=user_id,
        )

    def list(self, purpose: Purpose | None = None) -> list[Prompt]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if purpose is None:
                cursor.execute("SELECT * FROM prompts")
            else:
                cursor.execute("SELECT * FROM prompts WHERE purpose = ?", (purpose,))
            return [self._row_to_prompt(row) for row in cursor.fetchall()]

    def get(self, prompt_id: PromptId) -> Prompt | None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
            row = cursor.fetchone()
            return self._row_to_prompt(row) if row else None

    def patch(self, prompt_id: PromptId, template: str, user_id: UserId) -> Prompt | None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
            row = cursor.fetchone()
            if row is None or row["user_id"] != user_id:
                return None
            new_version = row["version"] + 1
            cursor.execute('''
                UPDATE prompts SET template = ?, version = ? WHERE id = ?
            ''', (template, new_version, prompt_id))
            conn.commit()
            cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
            return self._row_to_prompt(cursor.fetchone())

    def set_active(self, user_id: UserId, purpose: Purpose, prompt_id: PromptId) -> Prompt | None:
        prompt = self.get(prompt_id)
        if prompt is None:
            return None
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO active_prompts (user_id, purpose, prompt_id)
                VALUES (?, ?, ?)
            ''', (user_id, purpose, prompt_id))
            conn.commit()
        return prompt

    def get_active(self, user_id: UserId, purpose: Purpose) -> Prompt | None:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.* FROM prompts p
                JOIN active_prompts ap ON p.id = ap.prompt_id
                WHERE ap.user_id = ? AND ap.purpose = ?
            ''', (user_id, purpose))
            row = cursor.fetchone()
            return self._row_to_prompt(row) if row else None

    def delete(self, prompt_id: PromptId, user_id: UserId) -> bool:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
            row = cursor.fetchone()
            if row is None or row["user_id"] != user_id:
                return False
            cursor.execute("DELETE FROM active_prompts WHERE prompt_id = ?", (prompt_id,))
            cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
            conn.commit()
            return True