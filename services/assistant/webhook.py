from fastapi import FastAPI, HTTPException
from providers import QueryRequest, ChatResponse
from agent import SmartGeminiAgent
from providers.state import app_state

app = FastAPI(title="SmartGeminiAgent API")
agent = SmartGeminiAgent()

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: QueryRequest):
    try:
        session = app_state.get_session(req.user_id)
        answer = agent.response(req.query, user_id=req.user_id, session=session)

        session["last_answer"] = answer

        return ChatResponse(
            user_id=req.user_id,
            query=req.query,
            response=answer
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# How to run swagger UI
# cd gemini-agent-chat/services/assistant
# uvicorn webhook:app --reload --host 0.0.0.0 --port 8000
# paste the below url into your browse:
# http://localhost:8000/docs