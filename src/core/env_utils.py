import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent


def get_env_file_path():
    """
    Determina qué archivo .env cargar según la variable ENV_FILE.

    - En desarrollo: export ENV_FILE=.bbvaclient.env
    - En producción: usa .env por defecto
    """
    env_file = os.getenv("ENV_FILE", ".env")
    env_file_path = ROOT_DIR / env_file
    if not env_file_path.exists():
        # In Docker, the variables are already loaded by docker-compose
        # If the file does not exist but we have API_KEY, it means it has already been loaded
        if os.getenv("API_KEY"):
            return env_file
        raise FileNotFoundError(f"Configuration file not found at {env_file_path}")
    return env_file_path
