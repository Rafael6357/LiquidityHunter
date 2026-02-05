import logging
import pandas as pd
from core.coinex_client import CoinExClient
from core.risk_manager import RiskManager
from core.order_executor import OrderExecutor
from modules.pattern_detector import PatternDetector
from modules.notifier import TelegramNotifier

logger = logging.getLogger(__name__)

class TradingStrategy:
    """Orquestador de la estrategia institucional para CoinEx."""

    def __init__(self, symbols, risk_per_trade=1.0):
        self.symbols = symbols
        self.client = CoinExClient()
        self.risk = RiskManager(risk_per_trade)
        self.executor = OrderExecutor(self.client)
        self.detector = PatternDetector()
        self.notifier = TelegramNotifier()

    def run_cycle(self):
        """Ejecuta un ciclo completo de análisis y trading en CoinEx."""
        if not self.client.connect():
            return

        for symbol in self.symbols:
            try:
                self._analyze_and_trade(symbol)
            except Exception as e:
                logger.error(f"Error analizando {symbol}: {e}")

    def _analyze_and_trade(self, symbol):
        # 1. Obtener datos (CoinEx usa timeframes como '15m' y '1h')
        df_m15 = self.client.get_rates(symbol, '15m', 100)
        df_h1 = self.client.get_rates(symbol, '1h', 50)
        
        if df_m15 is None or df_h1 is None:
            return

        # 2. Detección de patrones con ajustes validados en Backtest
        threshold = 0.35 # Umbral optimizado
        
        amd = self.detector.detect_amd_cycle(df_m15)
        if not amd or amd['status'] not in ['MANIPULATION_DETECTED', 'MANIPULATION_DOWN', 'MANIPULATION_UP', 'DISTRIBUTION_TREND']:
            return

        # 3. Lógica de entrada optimizada
        bias = amd['bias']
        latest_price = df_m15['close'].iloc[-1]
        
        # Obtener bloques de ambas temporalidades para mayor precisión
        obs_h1 = self.detector.detect_order_blocks(df_h1, displacement_threshold=threshold)
        obs_m15 = self.detector.detect_order_blocks(df_m15, displacement_threshold=threshold)
        all_obs = obs_h1 + obs_m15

        if bias == 'BULLISH':
            bullish_obs = [ob for ob in all_obs if ob['type'] == 'BULLISH_OB']
            if bullish_obs:
                ob = bullish_obs[-1]
                # Validación de mitigación y SL lógico
                if ob['low'] < latest_price and latest_price <= ob['high'] * 1.015:
                    sl = ob['low']
                    risk = latest_price - sl
                    tp = latest_price + (risk * 2.5)
                    
                    balance = self.client.get_balance('USDT')
                    risk_amount_usdt = balance * (self.risk.risk_per_trade / 100)
                    
                    if self.risk.validate_trade(symbol, 'buy', latest_price, sl, tp):
                        # Notificar siempre, independientemente del balance
                        logger.info(f"ALERTA INSTITUCIONAL EN {symbol} @ {latest_price}")
                        self.notifier.notify_trade(symbol, 'buy', latest_price, sl, tp)

                        # Intentar ejecutar solo si hay balance
                        if risk_amount_usdt > 0:
                            logger.info(f"EJECUTANDO COMPRA REAL EN {symbol}")
                            self.executor.execute_market_order(symbol, 'buy', risk_amount_usdt, latest_price, sl, tp)
                        else:
                            logger.warning(f"Operacion real omitida por falta de balance en USDT.")

        elif bias == 'BEARISH':
            bearish_obs = [ob for ob in all_obs if ob['type'] == 'BEARISH_OB']
            if bearish_obs:
                ob = bearish_obs[-1]
                # Validación de mitigación y SL lógico
                if ob['high'] > latest_price and latest_price >= ob['low'] * 0.985:
                    sl = ob['high']
                    risk = sl - latest_price
                    tp = latest_price - (risk * 2.5)
                    
                    balance = self.client.get_balance('USDT')
                    amount_crypto = self.risk.calculate_amount(symbol, balance, latest_price)
                    
                    if self.risk.validate_trade(symbol, 'sell', latest_price, sl, tp):
                        # Notificar siempre
                        logger.info(f"ALERTA INSTITUCIONAL EN {symbol} @ {latest_price}")
                        self.notifier.notify_trade(symbol, 'sell', latest_price, sl, tp)

                        # Intentar ejecutar solo si hay balance
                        if amount_crypto > 0:
                            logger.info(f"EJECUTANDO VENTA REAL EN {symbol}")
                            self.executor.execute_market_order(symbol, 'sell', amount_crypto, latest_price, sl, tp)
                        else:
                            logger.warning(f"Operacion real omitida por falta de balance.")

    def _calculate_crypto_amount(self, symbol, price):
        # Este método ya no es necesario, se usa self.risk.calculate_amount
        pass
