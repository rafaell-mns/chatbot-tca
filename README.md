# Chatbot multiusuário

Trabalho final da disciplina Tópicos em Computação Aplicada (UFPI, 2026.2).

Aplicação de chatbot em que vários usuários conversam ao mesmo tempo. Cada usuário recebe um ID de sessão único (UUID) no momento em que se conecta, e o histórico de cada conversa é mantido isolado das demais.

**Endpoint público:** `http://SEU-ENDERECO-EC2:8000` *(preencher com o endereço da instância EC2)*

**Documentação interativa (Swagger):** `http://SEU-ENDERECO-EC2:8000/docs`

## Como funciona

1. O cliente chama `POST /sessions` e recebe um `session_id` (UUID).
2. A cada pergunta, o cliente chama `POST /chat` enviando o `session_id` e a mensagem.
3. O servidor acrescenta a mensagem ao histórico daquela sessão, envia o histórico ao modelo de linguagem e devolve a resposta.
4. Sessões diferentes nunca compartilham histórico.

## Tecnologias e justificativas

| Parte | Escolha | Por quê |
|---|---|---|
| Backend | Python + FastAPI | Suporta concorrência com `async`, gera a documentação da API automaticamente e tem validação de dados embutida. |
| Servidor | Uvicorn | Servidor ASGI que acompanha o FastAPI. |
| LLM | OpenRouter | Uma única API dá acesso a vários modelos, inclusive gratuitos, sem custo para o projeto. |
| Modelo | `openrouter/free` | Roteador do OpenRouter que escolhe um modelo gratuito disponível. É possível fixar uma lista de modelos pela variável `LLM_MODELS`. |
| Sessões | UUID + dicionário em memória | O enunciado aceita histórico efêmero, e a solução evita dependências extras. |
| Frontend | HTML, CSS e JavaScript puros | Interface de chat simples, sem etapa de build. |

### Decisões técnicas

- **Concorrência:** a chamada ao LLM é síncrona e roda em `asyncio.to_thread`, então uma resposta lenta de um usuário não trava os outros.
- **Lock por sessão:** mensagens da mesma sessão são processadas em ordem, e sessões diferentes não se bloqueiam.
- **Tolerância a falhas:** se um modelo falhar ou responder vazio, o servidor tenta o próximo da lista `LLM_MODELS`. Se todos falharem, a API devolve o erro 502.
- **Limite de contexto:** só as últimas 20 mensagens do histórico são enviadas ao modelo, e cada chamada tem timeout de 45 segundos.
- **Histórico em memória:** ele é perdido se o servidor reiniciar. Por isso o servidor deve rodar com **1 worker** do Uvicorn. Se a sessão deixar de existir, a API responde 404 e o frontend cria uma nova automaticamente.

## Estrutura do repositório

```
chatbot-tca/
├── backend/
│   ├── main.py               # app FastAPI, CORS e rota /health
│   ├── routes.py             # rotas da API
│   ├── session_manager.py    # sessões em memória (UUID, histórico, lock)
│   ├── llm_service.py        # integração com o OpenRouter
│   ├── test_concorrencia.py  # teste com vários usuários simultâneos
│   └── requirements.txt
├── frontend/
│   └── index.html            # interface de chat
├── .env.example
└── README.md
```

## Como rodar localmente

Pré-requisito: Python 3.11 ou superior.

**1. Clonar o repositório**

```
git clone https://github.com/rafaell-mns/chatbot-tca.git
cd chatbot-tca
```

**2. Criar o arquivo `.env` na raiz do projeto**

Copie o `.env.example` para `.env` e preencha a chave:

```
OPENROUTER_API_KEY=sua_chave_aqui
LLM_MOCK=0
LLM_MODELS=openrouter/free
```

| Variável | Para que serve |
|---|---|
| `OPENROUTER_API_KEY` | Chave da API do OpenRouter (https://openrouter.ai). |
| `LLM_MOCK` | Com `1`, o servidor usa respostas simuladas, sem chamar o LLM. Útil para testes de carga. |
| `LLM_MODELS` | Lista de modelos separados por vírgula, em ordem de prioridade. |

O arquivo `.env` não vai para o GitHub (está no `.gitignore`).

**3. Instalar as dependências e iniciar o backend**

```
cd backend
python -m venv venv
venv\Scripts\activate          # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

O servidor sobe em `http://127.0.0.1:8000`. A documentação interativa fica em `http://127.0.0.1:8000/docs`.

**4. Abrir o frontend**

Abra o arquivo `frontend/index.html` no navegador. No topo do script existe a constante `API_URL`, que deve apontar para o backend (por padrão, `http://127.0.0.1:8000`).

## Documentação da API

URL base: `http://SEU-ENDERECO-EC2:8000`

### POST /sessions

Cria uma sessão e devolve o ID único.

```
curl -X POST http://SEU-ENDERECO-EC2:8000/sessions
```

Resposta (200):

```json
{ "session_id": "04daf7df-8d3a-4c26-930c-2f24a0eefcf6" }
```

### POST /chat

Envia uma pergunta dentro de uma sessão e recebe a resposta do modelo.

Corpo da requisição:

```json
{ "session_id": "04daf7df-8d3a-4c26-930c-2f24a0eefcf6", "message": "Olá! Pode me ajudar a organizar meus estudos?" }
```

```
curl -X POST http://SEU-ENDERECO-EC2:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "COLE-O-ID-AQUI", "message": "Olá!"}'
```

Resposta (200):

```json
{ "session_id": "04daf7df-8d3a-4c26-930c-2f24a0eefcf6", "reply": "Olá! Claro, vamos organizar..." }
```

### GET /sessions/{session_id}/history

Devolve o histórico da sessão.

```
curl http://SEU-ENDERECO-EC2:8000/sessions/COLE-O-ID-AQUI/history
```

Resposta (200):

```json
{
  "history": [
    { "role": "user", "content": "Olá!" },
    { "role": "assistant", "content": "Olá! Como posso ajudar?" }
  ]
}
```

### DELETE /sessions/{session_id}

Apaga a sessão e o histórico dela.

```
curl -X DELETE http://SEU-ENDERECO-EC2:8000/sessions/COLE-O-ID-AQUI
```

Resposta (200):

```json
{ "deleted": true }
```

### GET /health

Verifica se o servidor está no ar. Resposta: `{ "status": "ok" }`.

### Códigos de erro

| Código | Quando acontece |
|---|---|
| 404 | A sessão não existe (ID errado, ou o servidor reiniciou). Crie outra com `POST /sessions`. |
| 422 | Corpo inválido, por exemplo `message` vazia ou ausente. |
| 502 | O modelo de linguagem falhou. A pergunta é removida do histórico, e o cliente pode tentar de novo. |

As respostas de erro vêm no formato `{ "detail": "mensagem explicando o problema" }`.

> **Windows (PowerShell):** use `curl.exe` no lugar de `curl`, e troque as aspas simples do JSON por aspas duplas escapadas, ou use o Swagger em `/docs`.

## Teste de concorrência

O script `backend/test_concorrencia.py` simula vários usuários ao mesmo tempo e confere se cada sessão tem UUID próprio e histórico isolado.

```
cd backend
python test_concorrencia.py http://127.0.0.1:8000 20
```

O último número é a quantidade de usuários simultâneos. Para testar sem gastar chamadas ao LLM, inicie o servidor com `LLM_MOCK=1` no `.env`.

## Publicação na AWS EC2

O backend roda em uma instância EC2 com o comando:

```
uvicorn main:app --host 0.0.0.0 --port 8000
```

A porta 8000 está liberada no Security Group. Mantenha **um único worker**, porque as sessões ficam na memória do processo.

## Equipe

*Bernardo Cavalcante
Cauã Martins
Francisco Rafael
Samara Feitosa*