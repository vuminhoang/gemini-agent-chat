from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
from typing import Any, List, Union
from agent import SmartGeminiAgent
from providers.state import AppState

# Define request and response schemas
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

# Initialize FastAPI app and the agent
app = FastAPI()
agent = SmartGeminiAgent()
app_logger = logging.getLogger(__name__)


async def get_app_state_with_user(request: Request) -> AppState:
    """
    Dependency to build AppState and attach user_id from headers or cookies.
    """
    # Instantiate AppState (or call existing factory if you have one)
    state = AppState()
    user_id = request.headers.get("X-User-ID") or request.cookies.get("user_id")
    # Attach to state
    setattr(state, "user_id", user_id)
    return state

@app.post(
    "/chat",
    response_model=QueryResponse,
    summary="Chat endpoint using SmartGeminiAgent",
    description="Takes a JSON body with 'query' and returns the agent's response, preserving user_id in AppState."
)
async def chat_endpoint(
    request_data: QueryRequest,
    app_state: AppState = Depends(get_app_state_with_user),
    request: Request = None,
):
    """
    REST API endpoint that takes a JSON payload with 'query',
    injects AppState (including user_id), and calls the agent.
    """
    try:
        # Log request
        app_logger.info(f"Received query from user {app_state.user_id}: {request_data.query}")
        # Call the agent, passing user_id if supported
        # answer = agent.response(request_data.query, user_id=app_state.user_id)
        answer = agent.response(request_data.query)
        return QueryResponse(response=answer)
    except Exception as e:
        app_logger.error(f"Error in chat_endpoint for user {app_state.user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("webhook:app", host="0.0.0.0", port=8000, reload=True)
