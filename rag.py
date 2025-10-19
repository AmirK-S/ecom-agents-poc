# rag.py
import os
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions

CSV_PATH   = os.getenv("ADS_CSV", "data/ads.csv")
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma")
COLLECTION = "ads_collection"
EMB_MODEL  = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

if not OPENAI_KEY:
    raise RuntimeError("OPENAI_API_KEY manquant pour les embeddings. Défini-le dans l'env.")

embed_fn = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_KEY,
    model_name=EMB_MODEL
)

_client = chromadb.PersistentClient(path=CHROMA_DIR)

def _row_to_text(row: dict) -> str:
    # Concat lisible pour l’indexation
    parts = []
    if row.get("secteur"): parts.append(f"secteur: {row['secteur']}")
    if row.get("hook_ou_angle"): parts.append(f"angle: {row['hook_ou_angle']}")
    if row.get("texte_publicitaire"): parts.append(f"texte: {row['texte_publicitaire']}")
    if row.get("call_to_action"): parts.append(f"cta: {row['call_to_action']}")
    return " | ".join(parts) if parts else "ad: n/a"

def _normalize_meta(row: dict) -> dict:
    # Garde les noms FR + crée des alias EN pour la logique du main
    meta = {
        "xid": row.get("xid", ""),
        "secteur": row.get("secteur", ""),
        "hook_ou_angle": row.get("hook_ou_angle", ""),
        "texte_publicitaire": row.get("texte_publicitaire", ""),
        "call_to_action": row.get("call_to_action", "")
    }
    # alias
    meta["sector"] = meta["secteur"]
    meta["angle"]  = meta["hook_ou_angle"]
    meta["text"]   = meta["texte_publicitaire"]
    meta["cta"]    = meta["call_to_action"]
    return meta

def build_or_update_index() -> int:
    if not os.path.exists(CSV_PATH):
        return 0
    # lecture robuste
    try:
        df = pd.read_csv(CSV_PATH)
    except UnicodeDecodeError:
        df = pd.read_csv(CSV_PATH, encoding="utf-8", errors="ignore")
    df = df.fillna("")

    # vérifie colonnes minimales
    required = {"secteur", "hook_ou_angle", "texte_publicitaire", "call_to_action"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans {CSV_PATH}: {', '.join(sorted(missing))}")

    # reset collection à chaque build POC (simple et idempotent)
    try:
        _client.delete_collection(COLLECTION)
    except Exception:
        pass
    coll = _client.get_or_create_collection(COLLECTION, embedding_function=embed_fn)

    docs, metas, ids = [], [], []
    for i, row in df.iterrows():
        rowd = row.to_dict()
        doc  = _row_to_text(rowd)
        meta = _normalize_meta(rowd)
        rid  = str(rowd.get("xid") or f"ad_{i}")
        docs.append(doc); metas.append(meta); ids.append(rid)

    if docs:
        coll.add(documents=docs, metadatas=metas, ids=ids)
    return len(docs)

def search_similar(query: str, n: int = 3):
    coll = _client.get_or_create_collection(COLLECTION, embedding_function=embed_fn)
    if coll.count() == 0:
        return []
    res = coll.query(query_texts=[query], n_results=n)
    out = []
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    for doc, meta in zip(docs, metas):
        out.append({"doc": doc, "meta": meta})
    return out
