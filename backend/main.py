
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

load_dotenv()

from routes import router

app = FastAPI(title="Chatbot Multiusuário", version="1.0")

# Localiza a interface HTML na pasta frontend
FRONTEND_INDEX = (
    Path(__file__).resolve().parent.parent
    / "frontend"
    / "index.html"
)


@app.get("/", include_in_schema=False)
def pagina_inicial():
    return FileResponse(FRONTEND_INDEX)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
