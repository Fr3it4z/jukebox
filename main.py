import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

import spotipy
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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

# De quantos em quantos segundos perguntamos ao Spotify
POLL_INTERVAL = 5

# Estado central: o loop escreve aqui, os endpoints leem daqui
state = {"active": False}

# Ecrãs ligados ao WebSocket, para o loop saber a quem enviar
clients = set()


def read_spotify():
    """Pergunta ao Spotify o que está a tocar e devolve um dicionário simples."""
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


async def broadcast(message):
    """Envia a mensagem a todos os ecrãs ligados."""
    # list() faz uma cópia, porque podemos remover clientes durante o ciclo
    for client in list(clients):
        try:
            await client.send_json(message)
        except Exception:
            # Ligação morta (ecrã fechado sem avisar): esquece este cliente
            clients.discard(client)


async def poll_spotify():
    """Loop em segundo plano: atualiza o estado de POLL_INTERVAL em POLL_INTERVAL segundos."""
    global state
    while True:
        try:
            # O spotipy é bloqueante, por isso corre numa thread à parte
            state = await asyncio.to_thread(read_spotify)
            # Envia sempre, mesmo sem mudar de música: assim o ecrã
            # corrige a interpolação do progresso a cada ciclo
            await broadcast(state)
        except Exception as error:
            # Sem rede ou erro do Spotify: avisa e tenta outra vez no próximo ciclo
            print(f"Erro ao ler o Spotify: {error}")
        await asyncio.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app):
    # Antes do yield: corre quando o servidor arranca
    task = asyncio.create_task(poll_spotify())
    yield
    # Depois do yield: corre quando o servidor desliga
    task.cancel()


app = FastAPI(lifespan=lifespan)


# --- Corre a cada pedido ---

@app.get("/now-playing")
def now_playing():
    return state


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)

    # Manda logo o estado atual, para o ecrã não ficar em branco até ao próximo ciclo
    await websocket.send_json(state)

    try:
        # Mantém a ligação aberta; o ecrã não manda nada, só recebe
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        # O ecrã fechou a ligação
        clients.discard(websocket)
