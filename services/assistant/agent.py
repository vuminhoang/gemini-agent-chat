import threading
from pathlib import Path
from typing import Dict, List, Any, Optional

import tomli
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
import logging
import prompt
from providers.state import app_state           # <─ NEW: dùng state chung (đã Redis)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class SmartGeminiAgent:
    def __init__(self):
        cfg = self._load_config()
        self.api_key = cfg.get("api_key", "")
        self.model_name = cfg.get("model_name", "gemini-pro")

        # LLM client (bọc trong lock vì client không thread‑safe 100 %)
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0.3,
            max_output_tokens=1024
        )
        self._llm_lock = threading.Lock()

        # ---------- tool setup ----------
        self.tools = self._setup_tools()
        self.tool_dict = {t.name: t for t in self.tools}
        self.tool_descriptions = prompt.get_tool_descriptions(self.tools)

    # ------------------- private helpers -------------------
    def _load_config(self) -> Dict:
        try:
            with open(Path("configs/dev.toml"), "rb") as f:
                cfg = tomli.load(f)
            return cfg.get("gemini", {})
        except Exception as e:
            logger.warning("Config load error: %s", e)
            return {}

    def _setup_tools(self) -> List[Tool]:
        def get_syllabus(lesson: str) -> str:
            # I hot fix it just for demo
            syllabus_text = """
            Giáo trình mini: “Nhập môn Thống kê cho DS”

            Mục tiêu
            - Hiểu khái niệm mẫu, tổng thể, độ lệch chuẩn.
            - Biết áp dụng phân bố chuẩn và t‑test khi phân tích dữ liệu nhỏ.

            Nội dung
            1. Thống kê mô tả – mean, median, variance.
            2. Luật số lớn và định lý giới hạn trung tâm.
            3. Ước lượng khoảng tin cậy và kiểm định giả thuyết (z‑test, t‑test).

            Bài tập
            - Tính mean và variance cho hai tập dữ liệu.
            - Viết script Python dùng scipy.stats thực hiện t‑test so sánh hai nhóm.
            """
            return syllabus_text
        return [Tool(name="get_syllabus",
                     func=get_syllabus,
                     description="Trả về giáo trình / lộ trình học cho bài học …")]

    def _decide_tool_use(self, query: str) -> dict:
        import json, re
        prompt_txt = prompt.TOOL_DECISION_PROMPT.format(
            system_prompt=prompt.SYSTEM_PROMPT,
            query=query,
            tool_descriptions=self.tool_descriptions
        )
        with self._llm_lock:
            resp = self.llm.invoke(prompt_txt).content
        json_text = re.search(r'\{.*\}', resp, re.S).group()
        try:
            return json.loads(json_text)
        except Exception:
            return {"use_tool": False, "tool_name": "", "tool_input": ""}

    # ------------------- public API -------------------
    def response(
        self,
        query: str,
        user_id: str = "default_user",
        session: Optional[Dict[str, Any]] = None
    ) -> str:

        # --- 1. lấy / cập nhật session ---
        session = session or app_state.get_session(user_id)
        app_state.append_history(user_id, "user", query)

        history_text = prompt.build_history_text(session["history"])
        meta = f"(User: {user_id})\n"  # session data nhỏ có thể thêm nếu cần

        # --- 2. quyết định tool ---
        decision = self._decide_tool_use(query)
        if decision["use_tool"] and decision["tool_name"] in self.tool_dict:
            tool_result = self.tool_dict[decision["tool_name"]].func(
                decision["tool_input"]
            )
            prompt_txt = prompt.TOOL_USE_PROMPT.format(
                system_prompt=prompt.SYSTEM_PROMPT,
                meta=meta,
                history=history_text,
                tool_name=decision["tool_name"],
                tool_result=tool_result
            )
        else:
            prompt_txt = prompt.NORMAL_PROMPT.format(
                system_prompt=prompt.SYSTEM_PROMPT,
                meta=meta,
                history=history_text,
                query=query
            )
        logger.info("Prompt: %s", prompt_txt)

        # --- 3. gọi model ---
        with self._llm_lock:
            answer = self.llm.invoke(prompt_txt).content
        logger.info("Answer: %s", answer)

        # --- 4. lưu lại ---
        app_state.append_history(user_id, "assistant", answer)
        return answer
