import tomli
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from typing import Dict, List, Any, Optional
import logging
import prompt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__)


class SmartGeminiAgent:
    def __init__(self):
        config = self._load_config()

        self.api_key = config.get("api_key", "")
        self.model_name = config.get("model_name", "gemini-pro")

        # Lưu trữ lịch sử theo từng user_id
        self.user_histories: Dict[str, List[Dict[str, str]]] = {}
        self.max_history = 2

        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0.3,
            max_output_tokens=1024
        )

        self.tools = self._setup_tools()

        # Create a dictionary for easy tool lookup by name
        self.tool_dict = {tool.name: tool for tool in self.tools}

        # Tool descriptions for prompt
        self.tool_descriptions = prompt.get_tool_descriptions(self.tools)

    def _load_config(self) -> Dict:
        """Lấy phần config gemini trong config toml"""
        try:
            config_path = Path("configs/dev.toml")
            with open(config_path, "rb") as f:
                config_data = tomli.load(f)

            # Extract relevant configurations
            if "gemini" in config_data:
                return config_data["gemini"]
            return {}
        except Exception as e:
            print(f"Error loading config file: {e}")
            return {}

    def _setup_tools(self) -> List[Tool]:
        """Set up tools for the agent to use."""

        def get_syllabus(lesson_string: str) -> str:
            """Chỗ này đang ném mặc định, về sau cần get data từ database"""
            return f"""Đây là giáo trình và hướng dẫn cho bài học: {lesson_string}.

MỤC TIÊU HỌC TẬP:
- Hiểu các khái niệm cơ bản về không gian vector
- Nắm vững các phép toán ma trận
- Giải quyết các hệ phương trình tuyến tính
- Ứng dụng đại số tuyến tính vào các bài toán thực tế

NỘI DUNG CHÍNH:
1. Không gian vector và ánh xạ tuyến tính
2. Ma trận và các phép toán ma trận
3. Hệ phương trình tuyến tính
4. Định thức và ma trận nghịch đảo
5. Giá trị riêng và vector riêng

BÀI TẬP:
- Phần bài tập cơ bản trang 45-50
- Phần bài tập nâng cao trang 51-55
- Bài tập thực hành trang 60-65

TÀI LIỆU THAM KHẢO:
- Đại số tuyến tính và ứng dụng - NXB Giáo Dục
- Linear Algebra and Its Applications - Gilbert Strang
"""

        tools = [
            Tool(
                name="get_syllabus",
                func=get_syllabus,
                description="Sử dụng khi người dùng hỏi về hướng dẫn giải bài học nào đó, thông tin về giáo trình hoặc lộ trình học "
            )
        ]

        return tools

    def _decide_tool_use(self, query: str) -> dict:
        tool_decision_prompt = prompt.TOOL_DECISION_PROMPT.format(
            system_prompt=prompt.SYSTEM_PROMPT,
            query=query,
            tool_descriptions=self.tool_descriptions
        )

        response = self.llm.invoke(tool_decision_prompt)

        try:
            response_text = response.content
            import json

            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].strip()

            decision = json.loads(response_text)
            return decision
        except Exception as e:
            print(f"Error parsing tool decision: {e}")
            return {"use_tool": False, "tool_name": "", "tool_input": ""}

    def get_user_history(self, user_id: str) -> List[Dict[str, str]]:
        """
        get history of user by user_id
        """
        if user_id not in self.user_histories:
            self.user_histories[user_id] = []
        return self.user_histories[user_id]

    def update_user_history(self, user_id: str, role: str, content: str):
        if user_id not in self.user_histories:
            self.user_histories[user_id] = []

        self.user_histories[user_id].append({"role": role, "content": content})

        if len(self.user_histories[user_id]) > self.max_history * 2:
            self.user_histories[user_id] = self.user_histories[user_id][-(self.max_history * 2):]

    def response(
            self,
            query: str,
            user_id: Optional[str] = None,
            session: Optional[Dict[str, Any]] = None
    ) -> str:
        try:
            if not user_id:
                user_id = "default_user"

            history = self.get_user_history(user_id)

            self.update_user_history(user_id, "user", query)

            meta = f"(User: {user_id})\nSession data: {session}\n" if session else ""

            history_text = prompt.build_history_text(history)

            decision = self._decide_tool_use(query)
            if decision["use_tool"] and decision["tool_name"] in self.tool_dict:
                tool_input = decision["tool_input"]
                tool_result = self.tool_dict[decision["tool_name"]].func(tool_input)

                # Sử dụng prompt với tool
                prompt_text = prompt.TOOL_USE_PROMPT.format(
                    system_prompt=prompt.SYSTEM_PROMPT,
                    meta=meta,
                    history=history_text,
                    tool_name=decision["tool_name"],
                    tool_result=tool_result
                )
                logger.info("Prompt: %s", prompt_text)
            else:
                # Sử dụng prompt thông thường
                prompt_text = prompt.NORMAL_PROMPT.format(
                    system_prompt=prompt.SYSTEM_PROMPT,
                    meta=meta,
                    history=history_text,
                    query=query
                )
                logger.info("Prompt: %s", prompt_text)

            answer = self.llm.invoke(prompt_text).content
            logger.info("Answer: %s", answer)

            # Thêm câu trả lời vào lịch sử
            self.update_user_history(user_id, "assistant", answer)

            return answer

        except Exception as e:
            logger.error(f"Error during agent execution: {e}")
            return f"Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn. Chi tiết lỗi: {str(e)}"


# Example usage
if __name__ == "__main__":
    agent = SmartGeminiAgent()

    question1 = "Tôi cần hướng dẫn về bài học Đại số tuyến tính"
    print(f"Alice hỏi: {question1}")
    print(f"Trả lời: {agent.response(question1, user_id='alice', session={})}")

    question2 = "Tôi muốn biết thêm về Giải tích"
    print(f"Bob hỏi: {question2}")
    print(f"Trả lời: {agent.response(question2, user_id='bob', session={})}")

    question3 = "Bạn có thể giải thích thêm về ma trận không?"
    print(f"Alice hỏi: {question3}")
    print(f"Trả lời: {agent.response(question3, user_id='alice', session={})}")