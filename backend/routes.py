import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from llm_service import gerar_resposta
from session_manager import sessions

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1)

@router.post("/sessions")
async def criar_sessao():
    #Gera o UUID no momento em que o cliente se conecta.
    session = sessions.create()
    return {"session_id": session.id}

@router.post("/chat")
async def chat(req: ChatRequest):
    session = sessions.get(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada. Crie uma com POST /sessions.")
    async with session.lock:
        session.history.append({"role": "user", "content": req.message})
        try:
            reply = await asyncio.to_thread(gerar_resposta, list(session.history))
        except Exception as exc:
            session.history.pop()  # desfaz a pergunta
            raise HTTPException(status_code=502, detail=f"Falha ao gerar resposta do LLM: {exc}")
        session.history.append({"role": "assistant", "content": reply})

    return {"session_id": session.id, "reply": reply}

@router.get("/sessions/{session_id}/history")
async def historico(session_id: str):
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    return {"history": session.history}

@router.delete("/sessions/{session_id}")
async def apagar_sessao(session_id: str):
    if not sessions.delete(session_id):
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    return {"deleted": True}