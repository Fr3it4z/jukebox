import os
from pathlib import Path
from dotenv import load_dotenv


# Localizar o .env
env_path = Path(__file__).resolve().parent / ".env"

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

print("Aprovado")