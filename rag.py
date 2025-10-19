# rag.py (robuste)
import os, pandas as pd

CSV_PATH   = os.getenv("ADS_CSV", "data/ads.csv")
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma")
COLLECTION = "ads_collection"
EMB_MODEL  = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

_use_rag = False
_coll = None

def _row_to_text(row: dict) -> str:
    parts = []
    if row.get("secteur"): parts.append(f"secteur: {row['secteur']}")
    if row.get("hook_ou_angle"): parts.append(f"angle: {row['hook_ou_angle']}")
    if row.get("texte_publicitaire"): parts.append(f"texte: {row['texte_publicitaire']}")
    if row.get("call_to_action"): parts.append(f"cta: {row['call_to_action']}")
    return " | ".join(parts) if parts else "ad: n/a"

def _normalize_meta(row: dict) -> dict:
    meta = {
        "id": row.get("xid") or row.get("id") or "",
        "secteur": row.get("secteur", ""),
        "hook_ou_angle": row.get("hook_ou_angle", ""),
        "texte_publicitaire": row.get("texte_publicitaire", ""),
        "call_to_action": row.get("call_to_action", "")
    }
    # alias pour le main
    meta["sector"] = meta["secteur"]
    meta["angle"]  = meta["hook_ou_angle"]
    meta["text"]   = meta["texte_publicitaire"]
    meta["cta"]    = meta["call_to_action"]
    return meta

def build_or_update_index() -> int:
    global _use_rag, _coll
    # préconditions
    if not OPENAI_KEY or not os.path.exists(CSV_PATH):
        _use_rag = False
        return 0

    try:
        df = pd.read_csv(CSV_PATH).fillna("")
    except Exception:
        _use_rag = False
        return 0

    required = {"secteur","hook_ou_angle","texte_publicitaire","call_to_action"}
    if not required.issubset(set(df.columns)):
        _use_rag = False
        return 0

    try:
        import chromadb
        from chromadb.utils import embedding_functions
        embed_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=OPENAI_KEY, model_name=EMB_MODEL
        )
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass
        _coll = client.get_or_create_collection(COLLECTION, embedding_function=embed_fn)

        docs, metas, ids = [], [], []
        for i, row in df.iterrows():
            rowd = row.to_dict()
            docs.append(_row_to_text(rowd))
            metas.append(_normalize_meta(rowd))
            rid = str(rowd.get("xid") or rowd.get("id") or f"ad_{i}")
            ids.append(rid)

        if docs:
            _coll.add(documents=docs, metadatas=metas, ids=ids)
            _use_rag = True
            return len(docs)
    except Exception:
        _use_rag = False
        return 0
    return 0

def search_similar(query: str, n: int = 3):
    if not _use_rag or _coll is None:
        return []
    try:
        res = _coll.query(query_texts=[query], n_results=n)
        out = []
        for doc, meta in zip(res.get("documents", [[]])[0], res.get("metadatas", [[]])[0]):
            out.append({"doc": doc, "meta": meta})
        return out
    except Exception:
        return []
