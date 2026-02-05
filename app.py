import threading
import os
import logging
from flask import Flask
from main import main

# Configurar logs básicos para Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RenderApp")

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Liquidity Hunter v3.0 esta vivo y monitoreando el mercado institucional.", 200

def start_bot():
    """Inicia el bot en un hilo separado."""
    logger.info("Iniciando el hilo del bot de trading...")
    bot_thread = threading.Thread(target=main, daemon=True)
    bot_thread.start()

# IMPORTANTE: Iniciamos el bot al importar el modulo
# Esto permite que funcione tanto con 'python app.py' como con 'gunicorn app:app'
start_bot()

if __name__ == "__main__":
    # Comando para ejecucion local
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
