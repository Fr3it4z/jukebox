import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pathlib import Path
from dotenv import load_dotenv


# Caminho para a pasta onde está este script
BASE_DIR = Path(__file__).resolve().parent

# Localizar o .env
env_path = BASE_DIR / ".env"

# Traz as variaveis de ambiente
load_dotenv(dotenv_path=env_path)

# Ler
config = {
    "SPOTIPY_CLIENT_ID": os.getenv("SPOTIPY_CLIENT_ID"),
    "SPOTIPY_CLIENT_SECRET": os.getenv("SPOTIPY_CLIENT_SECRET"),
    "SPOTIPY_REDIRECT_URI": os.getenv("SPOTIPY_REDIRECT_URI"),
}
#Confirmar que existem as variaveis de ambiente
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

# Pedir o estado atual do player
playback = sp.current_playback()
print(playback)
