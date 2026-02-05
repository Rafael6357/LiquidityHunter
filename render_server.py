import threading
import os
from flask import Flask
from main import main

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Liquidity Hunter v3.0 está vivo y monitoreando el mercado institucional.", 200

def run_bot():
    # Ejecutamos el bucle principal del bot en un hilo separado
    main()

if __name__ == "__main__":
    # 1. Iniciar el bot en segundo plano
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # 2. Iniciar servidor web para que Render no apague la instancia
    # Render asigna automáticamente un puerto en la variable de entorno PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
