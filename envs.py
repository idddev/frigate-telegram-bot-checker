import os

def get_env(name: str) -> str:
    """Obtiene la variable de entorno 'name' y lanza un error si no existe."""
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"La variable de entorno {name} no está definida.")
    return value

TELEGRAM_TOKEN = get_env("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = get_env("TELEGRAM_CHAT_ID")
LAST_PING_FILE = get_env("LAST_PING_FILE")
PING_TIMEOUT = int(get_env("PING_TIMEOUT"))
PING_INTERVAL = int(get_env("PING_INTERVAL"))
LAST_ALERT_FILE = get_env("LAST_ALERT_FILE")
ALERT_TIMEOUT = int(get_env("ALERT_TIMEOUT"))