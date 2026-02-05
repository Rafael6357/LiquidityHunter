import logging
import time
import os
from dotenv import load_dotenv
from modules.trading_strategy import TradingStrategy

# Configuración de Logging Profesional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trading_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LiquidityHunter")

def main():
    load_dotenv()
    
    pairs = os.getenv("PAIRS", "BTC/USDT,ETH/USDT,SOL/USDT").split(",")
    risk = float(os.getenv("RISK_PER_TRADE", "1.0"))
    
    logger.info("=== INICIANDO LIQUIDITY HUNTER v3.0 (CoinEx Institutional) ===")
    logger.info(f"Pares monitoreados: {pairs}")
    logger.info(f"Riesgo por operación: {risk}%")

    strategy = TradingStrategy(pairs, risk)
    
    # Enviar mensaje de bienvenida
    strategy.notifier.send_welcome()

    try:
        while True:
            strategy.run_cycle()
            # Esperar 5 minutos para la próxima vela M15 (aprox)
            time.sleep(300)
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario.")
    except Exception as e:
        logger.critical(f"Error fatal en el bot: {e}")

if __name__ == "__main__":
    main()
