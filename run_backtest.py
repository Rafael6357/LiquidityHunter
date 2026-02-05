import logging
import os
from dotenv import load_dotenv
from core.coinex_client import CoinExClient
from modules.backtester import Backtester

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BacktestRunner")

def run_historical_test():
    load_dotenv()
    pairs = os.getenv("PAIRS", "BTC/USDT,ETH/USDT,SOL/USDT").split(",")
    
    client = CoinExClient()
    # Conectamos en modo solo lectura para obtener datos
    client.connect()
    
    backtester = Backtester(initial_balance=1000.0, risk_per_trade=1.0)
    
    print("\n" + "="*50)
    print("INICIANDO SIMULACIÓN HISTÓRICA (BACKTEST)")
    print("="*50)

    for symbol in pairs:
        logger.info(f"Obteniendo datos históricos para {symbol}...")
        
        # Obtenemos datos suficientes para alinear ambas temporalidades
        df_m15 = client.get_rates(symbol, '15m', 500)
        df_h1 = client.get_rates(symbol, '1h', 200)
        
        if df_m15 is not None and df_h1 is not None:
            backtester.run(df_m15, df_h1, symbol)
        else:
            logger.error(f"No se pudieron obtener datos para {symbol}")

    print("="*50)
    print("SIMULACIÓN FINALIZADA")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_historical_test()
