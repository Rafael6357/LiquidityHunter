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
    """Inicia el bot en un hilo separado con un reporte de actividad."""
    logger.info("Iniciando el hilo del bot de trading...")
    
    def bot_loop_with_heartbeat():
        from modules.notifier import TelegramNotifier
        notifier = TelegramNotifier()
        
        # Enviar confirmación inicial
        notifier.send_message("[REPORTE] El bot ha iniciado correctamente en la nube.")
        
        last_heartbeat = 0
        while True:
            import time
            current_time = time.time()
            
            # Ejecutar ciclo de trading
            main()
            
            # Enviar un "estoy vivo" cada 12 horas (43200 segundos)
            if current_time - last_heartbeat > 43200:
                notifier.send_message("[REPORTE DE ACTIVIDAD] Liquidity Hunter sigue patrullando el mercado. Sin señales institucionales claras por ahora.")
                last_heartbeat = current_time
            
            # Esperar 5 minutos para el próximo ciclo
            time.sleep(300)

    bot_thread = threading.Thread(target=bot_loop_with_heartbeat, daemon=True)
    bot_thread.start()

# IMPORTANTE: Iniciamos el bot al importar el modulo
# Esto permite que funcione tanto con 'python app.py' como con 'gunicorn app:app'
start_bot()

if __name__ == "__main__":
    # Comando para ejecucion local
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
