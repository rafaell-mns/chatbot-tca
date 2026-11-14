# Chatbot multiusuário

Trabalho final da disciplina Tópicos em Computação Aplicada (UFPI, 2026.2).

Aplicação de chatbot em que vários usuários conversam ao mesmo tempo. Cada usuário recebe um ID de sessão único (UUID) quando se conecta, e o histórico de cada conversa fica isolado das demais.

## Sumário

1. [Acesso rápido](#acesso-rápido)
2. [Como funciona](#como-funciona)
3. [Tecnologias e decisões técnicas](#tecnologias-e-decisões-técnicas)
4. [Estrutura do repositório](#estrutura-do-repositório)
5. [Como rodar localmente](#como-rodar-localmente)
6. [Documentação da API](#documentação-da-api)
7. [Teste de concorrência](#teste-de-concorrência)
8. [Publicação](#publicação)
9. [Limitações conhecidas](#limitações-conhecidas)
10. [Equipe](#equipe)

## Acesso rápido

| O quê | Endereço |
|---|---|
| Interface de chat | https://chatbot-tca.onrender.com/ |
| Endpoint público da API | https://chatbot-tca.onrender.com |
| Documentação interativa (Swagger) | https://chatbot-tca.onrender.com/docs |
| Código-fonte | https://github.com/rafaell-mns/chatbot-tca |

> No plano gratuito do Render, o serviço entra em repouso depois de um tempo sem acessos. A primeira requisição depois disso pode levar mais de meio minuto.

### Teste rápido pela API

Em três comandos (no Prompt de Comando, Linux ou Mac):

```bash
# 1. Criar uma sessão e copiar o session_id da resposta
curl -X POST https://chatbot-tca.onrender.com/sessions

# 2. Fazer uma pergunta (troque COLE-O-ID-AQUI pelo session_id)
curl -X POST https://chatbot-tca.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "COLE-O-ID-AQUI", "message": "Olá!"}'

# 3. Ver o histórico da sessão
curl https://chatbot-tca.onrender.com/sessions/COLE-O-ID-AQUI/history
```

## Como funciona

1. O cliente chama `POST /sessions` e recebe um `session_id` (UUID).
2. A cada pergunta, o cliente chama `POST /chat` com o `session_id` e a mensagem.
3. O servidor acrescenta a mensagem ao histórico daquela sessão, envia o histórico ao modelo de linguagem e devolve a resposta.
4. Sessões diferentes nunca compartilham histórico.

## Tecnologias e decisões técnicas

### Escolhas

| Parte | Escolha | Por quê |
|---|---|---|
| Backend | Python + FastAPI | Suporta concorrência com `async`, gera a documentação da API automaticamente e valida os dados. |
| Servidor | Uvicorn | Servidor ASGI que acompanha o FastAPI. |
| LLM | OpenRouter | Uma única API dá acesso a vários modelos, inclusive gratuitos, sem custo para o projeto. |
| Modelo | `openrouter/free` | Roteador que escolhe um modelo gratuito disponível. A lista pode ser fixada pela variável `LLM_MODELS`. |
| Sessões | UUID + dicionário em memória | O enunciado aceita histórico efêmero, e a solução evita dependências extras. |
| Frontend | HTML, CSS e JavaScript puros | Interface simples, sem etapa de build. |

### Decisões técnicas

- **Concorrência:** a chamada ao LLM roda em `asyncio.to_thread`, então uma resposta lenta de um usuário não trava os outros.
- **Lock por sessão:** mensagens da mesma sessão são processadas em ordem, e sessões diferentes não se bloqueiam.
- **Tolerância a falhas:** se um modelo falhar ou responder vazio, o servidor tenta o próximo da lista `LLM_MODELS`. Se todos falharem, a API devolve o erro 502.
- **Limite de contexto:** só as últimas 20 mensagens do histórico são enviadas ao modelo, com timeout de 45 segundos por chamada.
- **Sessão perdida:** se a sessão deixar de existir, a API responde 404 e o frontend cria uma nova automaticamente.

## Estrutura do repositório

```text
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

### 1. Clonar o repositório

```bash
git clone https://github.com/rafaell-mns/chatbot-tca.git
cd chatbot-tca
```

### 2. Criar o arquivo `.env` na raiz do projeto

Copie o `.env.example` para `.env` e preencha a chave:

```text
OPENROUTER_API_KEY=sua_chave_aqui
LLM_MOCK=0
LLM_MODELS=openrouter/free
```

| Variável | Para que serve |
|---|---|
| `OPENROUTER_API_KEY` | Chave da API do OpenRouter (https://openrouter.ai). |
| `LLM_MOCK` | Com `1`, o servidor responde com texto simulado, sem chamar o LLM. Útil para testes de carga. |
| `LLM_MODELS` | Modelos separados por vírgula, em ordem de prioridade. |

O arquivo `.env` não vai para o GitHub (está no `.gitignore`).

### 3. Instalar as dependências e iniciar o backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

O servidor sobe em `http://127.0.0.1:8000`, e a documentação interativa fica em `http://127.0.0.1:8000/docs`.

### 4. Abrir a interface

Com o backend rodando, abra `http://127.0.0.1:8000/` no navegador. A interface (`frontend/index.html`) usa o mesmo endereço da API.

## Documentação da API

URL base: `https://chatbot-tca.onrender.com`

| Método | Rota | Descrição |
|---|---|---|
| POST | `/sessions` | Cria uma sessão |
| POST | `/chat` | Envia uma pergunta e recebe a resposta |
| GET | `/sessions/{session_id}/history` | Devolve o histórico da sessão |
| DELETE | `/sessions/{session_id}` | Apaga a sessão |
| GET | `/health` | Verifica se o servidor está no ar |

### POST /sessions

Cria uma sessão e devolve o ID único.

```bash
curl -X POST https://chatbot-tca.onrender.com/sessions
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

```bash
curl -X POST https://chatbot-tca.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "COLE-O-ID-AQUI", "message": "Olá!"}'
```

Resposta (200):

```json
{ "session_id": "04daf7df-8d3a-4c26-930c-2f24a0eefcf6", "reply": "Olá! Claro, vamos organizar..." }
```

### GET /sessions/{session_id}/history

Devolve o histórico da sessão.

```bash
curl https://chatbot-tca.onrender.com/sessions/COLE-O-ID-AQUI/history
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

```bash
curl -X DELETE https://chatbot-tca.onrender.com/sessions/COLE-O-ID-AQUI
```

Resposta (200):

```json
{ "deleted": true }
```

### GET /health

Verifica se o servidor está no ar.

```json
{ "status": "ok" }
```

### Códigos de erro

As respostas de erro vêm no formato `{ "detail": "mensagem explicando o problema" }`.

| Código | Quando acontece |
|---|---|
| 404 | A sessão não existe (ID errado, ou o servidor reiniciou). Crie outra com `POST /sessions`. |
| 422 | Corpo inválido, por exemplo `message` vazia ou ausente. |
| 502 | O modelo de linguagem falhou. A pergunta é removida do histórico, e o cliente pode tentar de novo. |

> **Windows:** os exemplos com `curl` funcionam no Prompt de Comando (cmd), no Linux e no Mac. No PowerShell, o `curl` é um apelido de outro comando e as aspas do JSON são alteradas. Nele, use o Swagger em `/docs` ou o comando `Invoke-RestMethod`.

## Teste de concorrência

O script `backend/test_concorrencia.py` simula vários usuários ao mesmo tempo e confere se cada sessão tem UUID próprio e histórico isolado.

```bash
cd backend
python test_concorrencia.py http://127.0.0.1:8000 20
```

O último número é a quantidade de usuários simultâneos. Para testar sem gastar chamadas ao LLM, inicie o servidor com `LLM_MOCK=1` no `.env`.

## Publicação

O backend está publicado como Web Service no Render, em https://chatbot-tca.onrender.com. A chave do OpenRouter e as demais variáveis (`OPENROUTER_API_KEY`, `LLM_MODELS`) ficam configuradas no painel do Render, e não no repositório.

Mantenha **um único worker**, porque as sessões ficam na memória do processo.

## Limitações conhecidas

- O histórico fica em memória: ele é perdido quando o servidor reinicia ou entra em repouso. Nesse caso, a interface cria uma sessão nova e avisa o usuário.
- O modelo `openrouter/free` escolhe modelos gratuitos, então a velocidade e o estilo das respostas podem variar entre uma mensagem e outra.
- No plano gratuito do Render, a primeira requisição depois de um período parado é lenta.

## Equipe

- Bernardo Cavalcante
- Cauã Martins
- Francisco Rafael
- Samara Feitosa
