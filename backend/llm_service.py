import time

def gerar_resposta(historico: list[dict]) -> str:
    time.sleep(1)  # simula a latência de um LLM, útil para testar concorrência
    ultima = historico[-1]["content"]
    turnos = sum(1 for m in historico if m["role"] == "user")
    return f"[mock] Você disse: '{ultima}' (mensagem {turnos} desta sessão)"