# ping_app.py
from envs import LAST_ALERT_FILE, LAST_PING_FILE, PING_INTERVAL, PING_TIMEOUT, PORT, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
import asyncio
import os
import logging
import requests
import uvicorn

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("ping_app")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    logger.error("Falta definir TELEGRAM_TOKEN o TELEGRAM_CHAT_ID en las variables de entorno.")

# Modelo de datos del payload de ping
class PingPayload(BaseModel):
    # Por ejemplo, un diccionario con datos por cada cámara.
    # Puedes ajustar la estructura según tus necesidades.
    cameras: dict

# Variable global para almacenar la última marca de tiempo del ping
last_ping_time: datetime | None = None

app = FastAPI()

@app.post("/ping")
async def ping(payload: PingPayload):
    global last_ping_time
    # Se guarda el timestamp actual
    last_ping_time = datetime.utcnow()
    # Escribir el timestamp en un archivo de texto
    try:
        with open(LAST_PING_FILE, "w") as f:
            f.write(last_ping_time.isoformat())
    except Exception as e:
        logger.error("Error escribiendo en %s: %s", LAST_PING_FILE, e)

    logger.info("Recibido ping a las %s. Payload: %s", last_ping_time.isoformat(), payload.dict())
    return {"status": "ok", "timestamp": last_ping_time.isoformat()}

def must_send_alert() -> bool:
    """
    Verifica si se debe enviar una alerta.
    """
    if not os.path.exists(LAST_ALERT_FILE):
        # Creamos el archivo de la última alerta si no existe
        with open(LAST_ALERT_FILE, "w") as f:
            f.write(datetime.utcnow().isoformat())
        return True
    
    try:
        with open(LAST_ALERT_FILE, "r") as f:
            last_ping_str = f.read().strip()
            last_ping_time = datetime.fromisoformat(last_ping_str)
    except Exception as e:
        logger.error("Error leyendo %s: %s", LAST_ALERT_FILE, e)
        return False
    elapsed = (datetime.utcnow() - last_ping_time).total_seconds()
    return elapsed > PING_TIMEOUT


def send_alert(message: str) -> None:
    """
    Envía una alerta por Telegram utilizando el API Bot.
    """
    # Validamos si tenemos que mandar la alerta
    if not must_send_alert():
        return
    
    # Guardamos la marca de tiempo de la última alerta
    try:
        with open(LAST_ALERT_FILE, "w") as f:
            f.write(datetime.utcnow().isoformat())
    except Exception as e:
        logger.error("Error escribiendo en %s: %s", LAST_ALERT_FILE, e)
        
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("No se puede enviar alerta. TELEGRAM_TOKEN o TELEGRAM_CHAT_ID no definidos.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        logger.info("Alerta enviada: %s", message)
    except Exception as e:
        logger.error("Error al enviar alerta: %s", e)

async def check_ping() -> None:
    """
    Tarea en segundo plano que revisa periódicamente si se ha recibido un ping.
    Si el último ping fue hace más de PING_TIMEOUT segundos, envía una alerta por Telegram.
    """
    global last_ping_time
    while True:
        await asyncio.sleep(PING_INTERVAL)
        now = datetime.utcnow()
        if last_ping_time is None:
            logger.warning("Aún no se ha recibido ningún ping.")
            continue
        elapsed = (now - last_ping_time).total_seconds()
        if elapsed > PING_TIMEOUT:
            alert_msg = f"ALERTA: No se ha recibido ping en {elapsed:.0f} segundos."
            logger.error(alert_msg)
            send_alert(alert_msg)
        else:
            logger.info("Ping actualizado hace %s segundos.", elapsed)

@app.on_event("startup")
async def startup_event() -> None:
    global last_ping_time
    # Leemos el ultimo ping si esta disponible
    if os.path.exists(LAST_PING_FILE):
        try:
            with open(LAST_PING_FILE, "r") as f:
                last_ping_str = f.read().strip()
                last_ping_time = datetime.fromisoformat(last_ping_str)
                logger.info("Último ping recibido a las %s.", last_ping_time.isoformat())
        except Exception as e:
            logger.error("Error leyendo %s: %s", LAST_PING_FILE, e)
            
    # Inicia la tarea en segundo plano para revisar pings
    asyncio.create_task(check_ping())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)