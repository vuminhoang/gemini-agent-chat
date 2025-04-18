from fastapi import Depends

class AppState:
    def __init__(self):
        # ví dụ lưu history hoặc context per user
        self.sessions: dict[str, dict] = {}

    def get_session(self, user_id: str) -> dict:
        # tạo mới nếu chưa có
        return self.sessions.setdefault(user_id, {})

# một instance toàn cục
app_state = AppState()