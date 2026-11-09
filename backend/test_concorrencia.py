import asyncio
import sys
import time
import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 10
MSGS = 3

async def usuario(client: httpx.AsyncClient, i: int) -> tuple[str, bool]:
    sid = (await client.post(f"{BASE}/sessions")).json()["session_id"]
    for k in range(MSGS):
        r = await client.post(f"{BASE}/chat", json={"session_id": sid, "message": f"user{i}-msg{k}"})
        r.raise_for_status()
    hist = (await client.get(f"{BASE}/sessions/{sid}/history")).json()["history"]
    users = [m["content"] for m in hist if m["role"] == "user"]
    ok = users == [f"user{i}-msg{k}" for k in range(MSGS)] and len(hist) == 2 * MSGS
    return sid, ok

async def main():
    inicio = time.perf_counter()
    async with httpx.AsyncClient(timeout=120) as client:
        resultados = await asyncio.gather(*(usuario(client, i) for i in range(N)))
    total = time.perf_counter() - inicio
    ids = {sid for sid, _ in resultados}
    isolados = sum(ok for _, ok in resultados)
    print(f"Usuários simultâneos : {N}")
    print(f"UUIDs distintos      : {len(ids)}/{N}")
    print(f"Históricos isolados  : {isolados}/{N}")
    print(f"Tempo total          : {total:.2f}s ({N * MSGS} requisições de chat)")
    print("RESULTADO:", "OK" if len(ids) == N and isolados == N else "FALHOU")

asyncio.run(main())