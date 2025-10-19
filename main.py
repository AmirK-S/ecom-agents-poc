import os, json
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# RAG (index CSV + recherche similaire)
from rag import build_or_update_index, search_similar

API_KEY = os.getenv("API_KEY", "")
ALLOW_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

def require_api_key(x_api_key: str = Header(default="")):
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if ALLOW_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

class Brief(BaseModel):
    product: str
    budget: str | None = None
    audience: str | None = None

@app.on_event("startup")
def _startup():
    try:
        n = build_or_update_index()
        print(f"[RAG] indexed {n} items from CSV")
    except Exception as e:
        print(f"[RAG] index error: {e}")

def _make_justification(query: str):
    try:
        hits = search_similar(query, n=3)
    except Exception as e:
        return {"evidence": [], "comment": f"RAG indisponible: {e}"}
    if not hits:
        return {"evidence": [], "comment": "Pas de données RAG disponibles."}
    evidence = []
    for h in hits:
        m = h.get("meta", {}) or {}
        evidence.append({
            "sector": m.get("sector") or m.get("category") or "n/a",
            "angle_hint": m.get("angle") or m.get("hook") or "",
        })
    return {"evidence": evidence, "comment": "Recommandations appuyées par des pubs similaires."}

@app.get("/")
def root():
    return {"Hello": "World"}

@app.get("/healthz")
def health():
    return {"ok": True}

def stub_generate(product: str, budget: str | None, audience: str | None):
    return {
        "source": "stub",
        "angles": ["UGC testimonial", "Storytelling avant/après"],
        "script": f"Hook: utilisateur montre {product} en 3s. Problème → solution → CTA.",
        "ad_text": f"Découvrez {product}. Résultats rapides. Essayez aujourd'hui."
    }

def openai_generate(product: str, budget: str | None, audience: str | None):
    from openai import OpenAI
    client = OpenAI()
    system = "Output ONLY valid JSON. Keys: angles(list[str],2), script(str), ad_text(str). No code fences."
    user = f"Product: {product}\nBudget: {budget}\nAudience: {audience}"
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    content = r.choices[0].message.content
    return {"source": "openai", **json.loads(content)}

@app.post("/generate")
@limiter.limit("10/minute")
def generate(brief: Brief, _: None = Depends(require_api_key)):
    justif = _make_justification(brief.product)
    has_key = bool(os.getenv("OPENAI_API_KEY"))
    if not has_key:
        out = stub_generate(brief.product, brief.budget, brief.audience)
        return {**out, "justification": justif}
    try:
        out = openai_generate(brief.product, brief.budget, brief.audience)
        return {**out, "justification": justif}
    except Exception:
        out = stub_generate(brief.product, brief.budget, brief.audience)
        return {**out, "justification": justif}
