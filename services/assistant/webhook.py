from fastapi import FastAPI, HTTPException
from providers import QueryRequest, ChatResponse
from agent import SmartGeminiAgent
from providers.state import app_state

app = FastAPI(title="SmartGeminiAgent API")
agent = SmartGeminiAgent()

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse, tags=["StudyWithMe"])
async def chat_endpoint(req: QueryRequest):
    try:
        answer = agent.response(req.query, user_id=req.user_id)

        session = app_state.get_session(req.user_id)
        session["last_answer"] = answer
        app_state.save_session(req.user_id, session)

        return ChatResponse(user_id=req.user_id,
                            query=req.query,
                            response=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

