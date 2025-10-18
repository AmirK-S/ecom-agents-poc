import os, json, re
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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
    has_key = bool(os.getenv("OPENAI_API_KEY"))
    if not has_key:
        return stub_generate(brief.product, brief.budget, brief.audience)
    try:
        return openai_generate(brief.product, brief.budget, brief.audience)
    except Exception as e:
        # fallback silencieux pour la démo
        return stub_generate(brief.product, brief.budget, brief.audience)
