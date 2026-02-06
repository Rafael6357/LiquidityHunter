import threading
import os
import logging
from flask import Flask
from main import main

from datetime import datetime

# Configurar logs básicos para Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RenderApp")

app = Flask(__name__)

@app.route('/')
@app.route('/ping')
def health_check():
    """Endpoint para que UptimeRobot haga ping y mantenga vivo el bot."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Ping recibido a las {now}")
    return {
        "status": "online",
        "message": "Liquidity Hunter v3.0 esta vivo y monitoreando el mercado institucional.",
        "timestamp": now
    }, 200

def start_bot():
    """Inicia el bot en un hilo separado con reinicio automático en caso de error."""
    logger.info("Iniciando el hilo del bot de trading...")
    
    def bot_thread_function():
        import time
        while True:
            try:
                logger.info("Llamando a la función main() del bot...")
                main()
            except Exception as e:
                logger.error(f"Error crítico en el hilo del bot: {e}")
                logger.info("Reiniciando el bot en 10 segundos...")
                time.sleep(10) # Esperar un poco antes de reiniciar para evitar bucles infinitos de error

    bot_thread = threading.Thread(target=bot_thread_function, daemon=True)
    bot_thread.start()

# IMPORTANTE: Iniciamos el bot al importar el modulo
# Esto permite que funcione tanto con 'python app.py' como con 'gunicorn app:app'
start_bot()

if __name__ == "__main__":
    # Comando para ejecucion local
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
