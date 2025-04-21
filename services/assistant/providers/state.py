import os, json, redis, threading
from typing import Any

_lock = threading.Lock()
r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

class AppState:
    max_history = 2

    def _key(self, user_id: str) -> str:
        return f"session:{user_id}"

    def get_session(self, user_id: str) -> dict[str, Any]:
        data = r.get(self._key(user_id))
        if data:
            return json.loads(data)
        return {"history": []}

    def save_session(self, user_id: str, session: dict[str, Any]):
        r.set(self._key(user_id), json.dumps(session), ex=86400)  # TTL 24 h

    def append_history(self, user_id: str, role: str, content: str):
        with _lock:
            session = self.get_session(user_id)
            hist: list = session.setdefault("history", [])
            hist.append({"role": role, "content": content})
            hist[:] = hist[-self.max_history * 2 :]
            self.save_session(user_id, session)

app_state = AppState()