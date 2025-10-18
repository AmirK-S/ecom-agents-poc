from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI()

@app.get("/")
def root():
    return {"Hello": "World"}

@app.get("/healthz")
def health():
    return {"ok": True}

class Brief(BaseModel):
    product: str
    budget: str | None = None
    audience: str | None = None

def stub_generate(product: str, budget: str | None, audience: str | None):
    angle = "UGC testimonial"
    script = f"Hook: Real user shows {product} in 3s. Problem → solution → CTA."
    ad_text = f"Découvrez {product}. Résultats rapides. Essayez aujourd'hui."
    return {"source": "stub", "angles": [angle], "script": script, "ad_text": ad_text}

def openai_generate(product: str, budget: str | None, audience: str | None):
    from openai import OpenAI
    client = OpenAI()
    prompt = f"""You are a performance ad strategist for e-commerce.
Product: {product}
Budget: {budget}
Audience: {audience}
Return JSON with keys: angles (list of 2 short angles), script (30s video script), ad_text (primary text)."""
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    import json
    # try to parse JSON; if not JSON, wrap it
    txt = r.choices[0].message.content
    try:
        return {"source": "openai", **json.loads(txt)}
    except Exception:
        return {"source": "openai", "raw": txt}

@app.post("/generate")
def generate(brief: Brief):
    if os.getenv("OPENAI_API_KEY"):
        return openai_generate(brief.product, brief.budget, brief.audience)
    return stub_generate(brief.product, brief.budget, brief.audience)
