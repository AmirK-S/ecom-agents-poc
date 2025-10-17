# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"Hello": "World"}

@app.get("/healthz")
def health():
    return {"ok": True}

