# Ecom AI POC

Petit proof-of-concept d’un **agent IA spécialisé e-commerce**.
Backend en **FastAPI**, déployé sur **Coolify**, sécurisé par **clé API** et limité en débit avec **SlowAPI**.
Intégration d’un **CSV de pubs e-commerce** dans une base vectorielle (Chroma) pour fournir des justifications RAG.

---

## Fonctionnalités

* **/healthz** → vérification de l’état.
* **/generate** (POST) → génère des publicités à partir d’un produit/budget/audience.

  * Utilise OpenAI si `OPENAI_API_KEY` est défini.
  * Sinon renvoie une réponse stub.
  * Ajoute une **justification RAG** en se basant sur les pubs du CSV.

---

## CSV attendu

Fichier : `data/ads.csv`
Colonnes :

* `xid` : identifiant unique
* `secteur` : ex. skincare, fitness…
* `hook_ou_angle` : accroche ou angle marketing utilisé
* `texte_publicitaire` : texte de la publicité
* `call_to_action` : bouton ou phrase d’action

Chaque ligne représente une pub. Environ 30–50 suffisent pour un POC.

---

## Variables d’environnement

* `API_KEY` : clé secrète pour accéder à l’API (ex: `X-API-Key: ...`).
* `OPENAI_API_KEY` : clé OpenAI (si dispo).
* `ADS_CSV` : chemin vers le CSV (par défaut `data/ads.csv`).
* `CHROMA_DIR` : chemin local pour la base vectorielle (par défaut `/app/chroma`).
* `ALLOWED_ORIGINS` : origines autorisées pour CORS (séparées par des virgules).

---

## Exemple d’appel

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
      {"sector": "skincare", "angle_hint": "avant/après"}
    ],
    "comment": "Recommandations appuyées par des pubs similaires."
  }
}
```

---

## Déploiement avec Coolify

1. Repo GitHub avec `main.py`, `rag.py`, `requirements.txt`, `Dockerfile`, `data/ads.csv`.
2. Créer une Application dans Coolify (Dockerfile).
3. Configurer les variables d’environnement.
4. Déployer.