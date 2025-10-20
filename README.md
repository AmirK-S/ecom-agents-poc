# 🚀 Ecom AI POC

Proof-of-Concept d’un **backend IA pour la génération de publicités e-commerce**.
Ce projet montre la capacité à combiner **FastAPI + OpenAI + RAG (CSV + Chroma)** et à déployer le tout sur un VPS avec **Coolify**.

---

## 🔧 Architecture technique

* **Backend** : [FastAPI](https://fastapi.tiangolo.com/) exposant deux endpoints :

  * `GET /healthz` → check de santé.
  * `POST /generate` → génère une pub à partir d’un produit.

* **Sécurité** :

  * Accès protégé par clé d’API (`X-API-Key`).
  * Limitation de débit avec [SlowAPI](https://pypi.org/project/slowapi/) (10 requêtes/minute/IP).

* **IA** :

  * **OpenAI** (si `OPENAI_API_KEY` défini) → modèle `gpt-4o-mini` pour générer `angles`, `script`, `ad_text`.
  * **Stub fallback** (si pas de clé) → réponses statiques mais plausibles.

* **RAG (Retrieval-Augmented Generation)** :

  * Base CSV `data/ads.csv` (30–50 pubs e-commerce).
  * Colonnes :

    * `xid`, `secteur`, `hook_ou_angle`, `texte_publicitaire`, `call_to_action`.
  * Indexation dans [ChromaDB](https://docs.trychroma.com/) avec embeddings OpenAI.
  * À chaque génération, l’API ajoute une **justification** issue des pubs les plus proches du produit demandé.

* **Déploiement** :

  * Hébergé sur VPS Hostinger via [Coolify](https://coolify.io/).
  * Build Docker auto depuis repo Git.
  * Domaine : `https://ecomaipoc.amirks.eu`.
  * Certificat SSL automatique.

---

## 📂 Structure

```
.
├── main.py        # FastAPI + endpoints
├── rag.py         # Indexation CSV + recherche Chroma
├── requirements.txt
├── data/
│   └── ads.csv    # Dataset e-commerce (pubs réelles ou mock)
└── README.md
```

---

## ⚙️ Variables d’environnement

| Variable          | Description                                                    |
| ----------------- | -------------------------------------------------------------- |
| `API_KEY`         | Clé secrète pour sécuriser `/generate`                         |
| `OPENAI_API_KEY`  | Clé OpenAI (sinon stub)                                        |
| `ADS_CSV`         | Chemin vers le CSV (défaut: `data/ads.csv`)                    |
| `CHROMA_DIR`      | Répertoire pour stocker la base Chroma (défaut: `/app/chroma`) |
| `ALLOWED_ORIGINS` | CORS origins autorisées (séparées par des virgules)            |

---

## ▶️ Exemple d’appel

### Vérification santé

```bash
curl -s https://ecomaipoc.amirks.eu/healthz
```

→ `{"ok": true}`

### Génération de pub

```bash
curl -s -X POST https://ecomaipoc.amirks.eu/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <TA_CLE_API>" \
  -d '{"product":"Crème visage anti-acné","budget":"50€/j","audience":"18-30"}' | jq
```

Réponse type :

```json
{
  "source": "openai",
  "angles": ["UGC testimonial","Storytelling"],
  "script": "Hook: ...",
  "ad_text": "Découvrez ...",
  "justification": {
    "evidence": [
      {"sector": "skincare", "angle_hint": "storytelling"},
      {"sector": "fitness", "angle_hint": "avant/après"}
    ],
    "comment": "Recommandations appuyées par des pubs similaires."
  }
}
```

---

## 🔍 Ce qu’il se passe concrètement

1. Tu envoies un produit + budget + audience à `/generate`.

2. L’API :

   * vérifie la clé d’API.
   * applique le **rate limit**.
   * génère la pub via OpenAI (ou stub si clé absente).
   * interroge le **dataset CSV** avec Chroma pour trouver pubs similaires.
   * fusionne les résultats → réponse finale.

3. Tu reçois un JSON prêt à être utilisé pour un pitch, une pub test ou une démo client.

---

## ✅ Objectif du POC

* **Démontrer la valeur technique** :

  * Backend déployé et sécurisé.
  * Génération IA en production.
  * Couplage IA + dataset métier.

* **Prouver la différenciation** :
  Pas juste un chatbot générique, mais un **agent e-commerce intelligent**, qui s’appuie sur des données concrètes.
