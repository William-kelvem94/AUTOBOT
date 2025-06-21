import requests
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Usando modelo garantido para contas gratuitas
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY

def gemini_ask(prompt):
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    resp = requests.post(GEMINI_API_URL, json=data, headers=headers)
    if resp.ok:
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"[ERRO GEMINI] {resp.text}"
