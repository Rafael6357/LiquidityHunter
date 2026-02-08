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
    
    # Manejo de múltiples cuentas
    accounts = []
    # Cuenta principal
    main_key = os.getenv("COINEX_API_KEY")
    main_secret = os.getenv("COINEX_SECRET")
    if main_key and main_secret:
        accounts.append({'api_key': main_key, 'secret': main_secret})
    
    # Cuentas adicionales (formato: KEY1:SECRET1,KEY2:SECRET2)
    extra_accounts = os.getenv("COINEX_EXTRA_ACCOUNTS", "")
    if extra_accounts:
        for acc_str in extra_accounts.split(","):
            if ":" in acc_str:
                k, s = acc_str.split(":")
                accounts.append({'api_key': k.strip(), 'secret': s.strip()})

    logger.info("=== INICIANDO LIQUIDITY HUNTER v3.0 (CoinEx Institutional) ===")
    logger.info(f"Pares monitoreados: {pairs}")
    logger.info(f"Riesgo por operación: {risk}%")
    logger.info(f"Cuentas configuradas: {len(accounts)}")

    strategy = TradingStrategy(pairs, accounts, risk)
    
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
