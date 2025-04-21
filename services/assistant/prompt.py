
SYSTEM_PROMPT = """Bạn là trợ lý ảo thông minh. Hãy trả lời câu hỏi của người dùng một cách chính xác, 
đầy đủ và hữu ích. Nếu không biết câu trả lời, hãy trung thực và đừng bịa thông tin."""

TOOL_DECISION_PROMPT = """{system_prompt}

Câu hỏi của người dùng: "{query}"

Bạn có quyền truy cập vào các công cụ sau:
{tool_descriptions}

Hãy quyết định xem có nên sử dụng công cụ nào không để trả lời câu hỏi trên.

Chỉ trả lời theo định dạng JSON chính xác sau:
{{
    "use_tool": true/false,
    "tool_name": "tên công cụ nếu cần sử dụng, không có thì để trống",
    "tool_input": "thông tin đầu vào cho công cụ nếu cần, không có thì để trống"
}}

Chỉ trả lời JSON, không thêm giải thích."""


NORMAL_PROMPT = """{system_prompt}

{meta}{history}

User: "{query}"
Assistant: """


TOOL_USE_PROMPT = """{system_prompt}

{meta}{history}

>>> Kết quả từ tool `{tool_name}`:
{tool_result}

Hãy trả lời người dùng một cách rõ ràng và đầy đủ, kết hợp thông tin trên.
Trả lời tiếng Việt!"""


def get_tool_descriptions(tools):
    return "\n".join([f"- {tool.name}: {tool.description}" for tool in tools])


def build_history_text(history):
    return "\n".join(f"{m['role']}: {m['content']}" for m in history)