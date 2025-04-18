from pydantic import BaseModel

# define payload request
class QueryRequest(BaseModel):
    query: str
    user_id: str


# define payload response
class ChatResponse(BaseModel):
    user_id: str
    query: str
    response: str