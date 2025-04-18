import tomli
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from typing import Dict, List, Any, Optional


class SmartGeminiAgent:
    def __init__(self):
        config = self._load_config()

        self.api_key = config.get("api_key", "")
        self.model_name = config.get("model_name", "gemini-pro")

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
        self.tool_descriptions = "\n".join([
            f"- {tool.name}: {tool.description}" for tool in self.tools
        ])

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
                description="Sử dụng khi người dùng hỏi về hướng dẫn giải bài học nào đó"
            )
        ]

        return tools

    def _decide_tool_use(self, query: str) -> dict:
        """
        Let the LLM decide if a tool should be used.

        Returns:
            Dict with decision info
        """
        tool_decision_prompt = f"""
        Câu hỏi của người dùng: "{query}"

        Bạn có quyền truy cập vào các công cụ sau:
        {self.tool_descriptions}

        Hãy quyết định xem có nên sử dụng công cụ nào không để trả lời câu hỏi trên.

        Chỉ trả lời theo định dạng JSON chính xác sau:
        {{
            "use_tool": true/false,
            "tool_name": "tên công cụ nếu cần sử dụng, không có thì để trống",
            "tool_input": "thông tin đầu vào cho công cụ nếu cần, không có thì để trống"
        }}

        Chỉ trả lời JSON, không thêm giải thích.
        """

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

    def response(
        self,
        query: str,
        user_id: Optional[str] = None,
        session: Optional[Dict[str, Any]] = None
    ) -> str:
        try:
            decision = self._decide_tool_use(query)

            # metadata cho context
            meta = f"(User: {user_id})\nSession data: {session}\n" if user_id else ""

            if decision["use_tool"] and decision["tool_name"] in self.tool_dict:
                tool_input = decision["tool_input"]
                tool_result = self.tool_dict[decision["tool_name"]].func(tool_input)

                final_prompt = (
                    f"{meta}"
                    f"Người dùng đã hỏi: \"{query}\"\n\n"
                    f"Dựa trên câu hỏi, tôi đã tìm thấy thông tin sau:\n\n"
                    f"{tool_result}\n\n"
                    "Hãy trả lời người dùng một cách rõ ràng và đầy đủ, kết hợp thông tin trên để trả lời câu hỏi của họ.\n"
                    "Đưa ra gợi ý học tập nếu phù hợp.\n"
                    "Trả lời tiếng Việt!"
                )

                response = self.llm.invoke(final_prompt)
                return response.content
            else:
                prompt = (
                    f"{meta}"
                    "Hãy trả lời câu hỏi sau đây một cách đầy đủ và hữu ích:\n\n"
                    f"\"{query}\"\n"
                    "Trả lời tiếng Việt!"
                )

                response = self.llm.invoke(prompt)
                return response.content

        except Exception as e:
            print(f"Error during agent execution: {e}")
            return f"Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn. Chi tiết lỗi: {str(e)}"


# Example usage
if __name__ == "__main__":
    agent = SmartGeminiAgent()

    question = "Tôi cần hướng dẫn về bài học Đại số tuyến tính"
    print(f"Câu hỏi: {question}")
    print(f"Trả lời: {agent.response(question, user_id='alice', session={})}")
