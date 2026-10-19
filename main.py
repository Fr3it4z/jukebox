import os
from pathlib import Path

import spotipy
from dotenv import load_dotenv
from fastapi import FastAPI
from spotipy.oauth2 import SpotifyOAuth


# --- Corre uma vez, quando o servidor arranca ---

# Caminho para a pasta onde está este ficheiro
BASE_DIR = Path(__file__).resolve().parent

# Traz as variáveis de ambiente do .env
load_dotenv(dotenv_path=BASE_DIR / ".env")

config = {
    "SPOTIPY_CLIENT_ID": os.getenv("SPOTIPY_CLIENT_ID"),
    "SPOTIPY_CLIENT_SECRET": os.getenv("SPOTIPY_CLIENT_SECRET"),
    "SPOTIPY_REDIRECT_URI": os.getenv("SPOTIPY_REDIRECT_URI"),
}

# Confirmar que existem as variáveis de ambiente
missing = [
    name
    for name, value in config.items()
    if not value
]

if missing:
    raise RuntimeError(
        f"Faltam as seguintes variáveis de ambiente: {', '.join(missing)}"
    )

# Configurar autenticação OAuth do Spotify
auth_manager = SpotifyOAuth(
    client_id=config["SPOTIPY_CLIENT_ID"],
    client_secret=config["SPOTIPY_CLIENT_SECRET"],
    redirect_uri=config["SPOTIPY_REDIRECT_URI"],
    scope="user-read-playback-state user-modify-playback-state",
    cache_path=str(BASE_DIR / ".spotify_token"),
)

# Cliente que faz os pedidos à API
sp = spotipy.Spotify(auth_manager=auth_manager)

app = FastAPI()


# --- Corre a cada pedido ---

@app.get("/now-playing")
def now_playing():
    playback = sp.current_playback()

    # Nada a tocar: não é um erro, é um estado normal
    if playback is None or playback["item"] is None:
        return {"active": False}

    item = playback["item"]
    images = item["album"]["images"]

    return {
        "active": True,
        "is_playing": playback["is_playing"],
        "title": item["name"],
        "artists": ", ".join(artist["name"] for artist in item["artists"]),
        "album": item["album"]["name"],
        "cover_url": images[0]["url"] if images else None,
        "progress_ms": playback["progress_ms"],
        "duration_ms": item["duration_ms"],
    }
