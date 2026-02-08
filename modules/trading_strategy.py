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

    def __init__(self, symbols, accounts, risk_per_trade=1.0):
        """
        accounts: Lista de diccionarios [{'api_key': '...', 'secret': '...'}]
        """
        self.symbols = symbols
        self.risk_per_trade = risk_per_trade
        self.detector = PatternDetector()
        self.notifier = TelegramNotifier()
        
        # Crear clientes y ejecutores para cada cuenta
        self.account_clients = []
        for acc in accounts:
            client = CoinExClient(acc['api_key'], acc['secret'])
            self.account_clients.append({
                'client': client,
                'executor': OrderExecutor(client),
                'risk': RiskManager(risk_per_trade)
            })

    def run_cycle(self):
        """Ejecuta un ciclo completo de análisis y trading en CoinEx Futuros (Temporalidad M5)."""
        # Usamos el primer cliente solo para obtener datos del mercado
        if not self.account_clients:
            logger.error("No hay cuentas configuradas.")
            return

        base_client = self.account_clients[0]['client']
        
        for symbol in self.symbols:
            try:
                # 1. Obtener datos en temporalidad M5
                df_m5 = base_client.get_rates(symbol, '5m', 100)
                df_h1 = base_client.get_rates(symbol, '1h', 50)
                
                if df_m5 is None or df_h1 is None:
                    continue

                # 2. Detectar patrón común en M5
                threshold = 0.35
                amd = self.detector.detect_amd_cycle(df_m5)
                
                if not amd or amd['status'] not in ['MANIPULATION_DETECTED', 'MANIPULATION_DOWN', 'MANIPULATION_UP', 'DISTRIBUTION_TREND']:
                    continue

                # 3. Si hay patrón, intentar ejecutar en cada cuenta
                self._execute_for_all_accounts(symbol, df_m5, df_h1, amd)

            except Exception as e:
                logger.error(f"Error analizando {symbol}: {e}")

    def _execute_for_all_accounts(self, symbol, df_m5, df_h1, amd):
        bias = amd['bias']
        latest_price = df_m5['close'].iloc[-1]
        threshold = 0.35
        leverage = 5 # Apalancamiento máximo solicitado
        
        obs_h1 = self.detector.detect_order_blocks(df_h1, displacement_threshold=threshold)
        obs_m5 = self.detector.detect_order_blocks(df_m5, displacement_threshold=threshold)
        all_obs = obs_h1 + obs_m5

        # Lógica de señal compartida
        signal_to_notify = None

        if bias == 'BULLISH':
            bullish_obs = [ob for ob in all_obs if ob['type'] == 'BULLISH_OB']
            if bullish_obs:
                ob = bullish_obs[-1]
                if ob['low'] < latest_price and latest_price <= ob['high'] * 1.015:
                    sl = ob['low']
                    risk_val = latest_price - sl
                    tp = latest_price + (risk_val * 2.5)
                    signal_to_notify = ('buy', latest_price, sl, tp)

        elif bias == 'BEARISH':
            bearish_obs = [ob for ob in all_obs if ob['type'] == 'BEARISH_OB']
            if bearish_obs:
                ob = bearish_obs[-1]
                if ob['high'] > latest_price and latest_price >= ob['low'] * 0.985:
                    sl = ob['high']
                    risk_val = sl - latest_price
                    tp = latest_price - (risk_val * 2.5)
                    signal_to_notify = ('sell', latest_price, sl, tp)

        # Si hay señal, ejecutar en todas las cuentas y notificar una vez
        if signal_to_notify:
            side, price, sl, tp = signal_to_notify
            self.notifier.notify_trade(symbol, side, price, sl, tp)
            
            for acc_data in self.account_clients:
                client = acc_data['client']
                executor = acc_data['executor']
                risk_mgr = acc_data['risk']
                
                try:
                    # Configurar apalancamiento antes de operar
                    client.set_leverage(symbol, leverage)
                    
                    balance = client.get_balance('USDT')
                    # Calcular cantidad basada en balance, precio y apalancamiento
                    amount = risk_mgr.calculate_amount(symbol, balance, price, leverage)

                    if risk_mgr.validate_trade(symbol, side, price, sl, tp):
                        logger.info(f"Ejecutando en cuenta {client.api_key[:5]}... {symbol} (FUTUROS 5X)")
                        executor.execute_market_order(symbol, side, amount, price, sl, tp)
                except Exception as e:
                    logger.error(f"Error ejecutando en cuenta {client.api_key[:5]}: {e}")

    def _calculate_crypto_amount(self, symbol, price):
        # Este método ya no es necesario, se usa self.risk.calculate_amount
        pass
