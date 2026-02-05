import ccxt
import os
import logging
import pandas as pd
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class CoinExClient:
    """Cliente para la API de CoinEx usando CCXT."""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("COINEX_API_KEY")
        self.secret = os.getenv("COINEX_SECRET")
        
        self.exchange = ccxt.coinex({
            'apiKey': self.api_key.strip() if self.api_key else None,
            'secret': self.secret.strip() if self.secret else None,
            'enableRateLimit': True,
            'options': {
                'brokerId': 'LiquidityHunter',
                'createMarketBuyOrderRequiresPrice': False,
            }
        })
        
    def connect(self):
        """Verifica la conexión y las credenciales."""
        try:
            if self.api_key and self.secret:
                # CoinEx V2 en CCXT puede requerir configuraciones específicas
                # Intentamos una llamada simple para validar
                self.exchange.fetch_balance()
                logger.info("Conexión exitosa a CoinEx (Trading Real habilitado).")
                return True
            else:
                logger.warning("CoinEx API Keys no configuradas. Modo solo lectura.")
                return True # Permitir modo lectura para análisis
        except Exception as e:
            logger.error(f"Error de autenticación en CoinEx: {e}")
            logger.info("El bot continuará en modo solo lectura para análisis de mercado.")
            # Desactivar API Key para evitar errores de firma en cada llamada si la key está mal
            self.exchange.apiKey = None
            self.exchange.secret = None
            return True

    def get_rates(self, symbol, timeframe='15m', limit=100):
        """Obtiene datos históricos (OHLCV)."""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {e}")
            return None

    def get_balance(self, currency='USDT'):
        """Obtiene el balance de una moneda específica."""
        try:
            balance = self.exchange.fetch_balance()
            return balance.get('free', {}).get(currency, 0.0)
        except Exception as e:
            logger.error(f"Error obteniendo balance: {e}")
            return 0.0
