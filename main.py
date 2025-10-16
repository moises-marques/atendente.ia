# main.py
import os
import json
import random
from fastapi import FastAPI, Header
from pydantic import BaseModel
from dotenv import load_dotenv
import difflib
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Atendente IA - RoboBot (Modo Híbrido)")

origins = [
    "https://meu-robochat.netlify.app",  # URL do seu frontend
    "http://localhost:3000",  # se quiser testar localmente
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # quem pode acessar
    allow_credentials=True,
    allow_methods=["*"],    # GET, POST, etc
    allow_headers=["*"],    # headers
)


load_dotenv()

# ==========================
# 1) Carrega a chave de API e mostra mensagem
# ==========================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("ERRO: Variável OPENAI_API_KEY NÃO está definida ou o arquivo .env não foi lido.")
    print("Verifique se o arquivo .env está na pasta raiz e se o nome da variável está correto.")
else:
    print(f"SUCESSO: Chave de API carregada. Início: {OPENAI_API_KEY[:5]}... Fim: {OPENAI_API_KEY[-5:]}")

# CONFIG
USE_MOCK = os.getenv("USE_MOCK", "true").lower() in ("1", "true", "yes")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # continuará útil mais tarde
KB_FILE = "kb.json"  # arquivo de FAQ/knowlege base editável pelo cliente
LOG_FILE = "conversations.log"

# app = FastAPI(title="Atendente IA - RoboBot (Modo Híbrido)")

# Modelos de request/response
class MessageIn(BaseModel):
    message: str
    user_id: str | None = None  # opcional, útil pra logs/personalização

class MessageOut(BaseModel):
    reply: str
    meta: dict | None = None

# ---------- Utilities ----------
def log_message(user_id, user_msg, bot_reply, mode):
    entry = {
        "ts": datetime.utcnow().isoformat()+"Z",
        "user_id": user_id,
        "message": user_msg,
        "reply": bot_reply,
        "mode": mode
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def load_kb():
    if not os.path.exists(KB_FILE):
        # cria um KB mínimo de exemplo se não existir
        demo = [
            {"q":"horário de atendimento", "a":"Nosso horário é Segunda a Sexta das 9h às 18h."},
            {"q":"preço do plano básico", "a":"O plano básico custa R$ 39/mês. Temos descontos para annual."},
            {"q":"como cancelar", "a":"Para cancelar, acesse sua conta > Configurações > Cancelar assinatura."}
        ]
        with open(KB_FILE, "w", encoding="utf-8") as f:
            json.dump(demo, f, ensure_ascii=False, indent=2)
        return demo
    with open(KB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

KB = load_kb()

def kb_lookup(question, top_n=1, cutoff=0.5):
    # busca por similaridade simples (difflib)
    questions = [entry["q"] for entry in KB]
    matches = difflib.get_close_matches(question.lower(), questions, n=top_n, cutoff=cutoff)
    if matches:
        # devolve a primeira correspondente e a resposta
        matched_q = matches[0]
        for entry in KB:
            if entry["q"] == matched_q:
                return entry["a"], matched_q
    return None, None

# ---------- Mock response logic ----------
def mock_reply(user_msg: str):
    txt = user_msg.strip().lower()

    # 1) Teste rápido
    if txt == "teste":
        return "🧩 Modo teste: o servidor está funcionando perfeitamente!", {"type":"test"}

    # 2) Intenções de ação simuladas (criando ticket, verificando pedido, etc)
    if any(w in txt for w in ("abrir chamado","criar ticket","abrir ticket","abrir chamado")):
        ticket_id = f"T-{random.randint(1000,9999)}"
        reply = f"✅ Chamado criado com sucesso. ID: {ticket_id}. Nosso time responderá em até 24h."
        return reply, {"type":"action", "action":"create_ticket", "ticket_id":ticket_id}

    if "status do pedido" in txt or ("status" in txt and "pedido" in txt):
        # resposta simulada
        reply = "O pedido #1234 está em transporte e deve chegar em 3 dias úteis."
        return reply, {"type":"action","action":"check_order","order_id":"1234"}

    # 3) Saudação e small talk
    if any(g in txt for g in ("olá","oi","bom dia","boa tarde","boa noite","fala")):
        return "Olá! Eu sou o RobôBot. Como posso ajudar você hoje?", {"type":"small_talk"}

    # 4) Busca na KB (FAQ)
    kb_answer, matched_q = kb_lookup(txt, top_n=1, cutoff=0.5)
    if kb_answer:
        return kb_answer, {"type":"kb", "matched_q": matched_q}

    # 5) Regras simples por palavras-chave
    if "preço" in txt or "valor" in txt or "custo" in txt:
        return "Temos planos que começam em R$ 39/mês. Quer que eu envie os detalhes por e-mail?", {"type":"pricing"}

    # 6) Fallback "inteligente" do mock (mais natural)
    fallback_variants = [
        "Desculpe — não entendi completamente. Pode dizer de outro jeito?",
        "Posso ajudar com: 'abrir chamado', 'préços', 'horário de atendimento' ou 'status do pedido'.",
        "Ainda não sei isso, quer que eu crie um chamado para a equipe humana?"
    ]
    return random.choice(fallback_variants), {"type":"fallback"}

# ---------- Endpoint ----------
@app.post("/chat", response_model=MessageOut)
async def chat_endpoint(body: MessageIn):
    x_openai_key: str | None = Header(None)  # <-- aqui você declara o header
    user_msg = body.message
    user_id = body.user_id or "anon"

     # ===============================
    # NOVO: verifica se veio chave do front-end
    # ===============================
    effective_api_key = x_openai_key or OPENAI_API_KEY  # se cliente passar chave, usa ela

    if effective_api_key and not USE_MOCK:
        # aqui entra a chamada real para OpenAI usando a chave do cliente
        # por enquanto, só placeholder
        reply = f"✅ Modo inteligente ativado! Chave recebida: {effective_api_key[:5]}... (não mostrada toda por segurança)"
        log_message(user_id, user_msg, reply, mode="openai")
        return {"reply": reply, "meta": {"mode":"openai"}}


    if USE_MOCK:
        reply, meta = mock_reply(user_msg)
        log_message(user_id, user_msg, reply, mode="mock")
        return {"reply": reply, "meta": meta}

    # caso não esteja em mock, aqui você colocaria a chamada real à OpenAI / RAG
    # por enquanto, um fallback claro
    reply = "⚠️ Modo real não habilitado. Configure USE_MOCK=false e a integração com LLM."
    log_message(user_id, user_msg, reply, mode="disabled")
    return {"reply": reply, "meta": {"mode":"disabled"}}

