from pydantic import BaseModel

# define payload request
class QueryRequest(BaseModel):
    user_id: str
    query: str

# define payload response
class ChatResponse(BaseModel):
    user_id: str
    query: str
    response: str