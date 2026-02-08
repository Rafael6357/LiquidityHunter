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
        """Ejecuta un ciclo completo de análisis y trading (SMC M5 y Unger M30)."""
        if not self.account_clients:
            logger.error("No hay cuentas configuradas.")
            return

        base_client = self.account_clients[0]['client']
        
        for symbol in self.symbols:
            try:
                # --- ESTRATEGIA 1: SMC (M5) ---
                df_m5 = base_client.get_rates(symbol, '5m', 100)
                df_h1 = base_client.get_rates(symbol, '1h', 50)
                
                if df_m5 is not None and df_h1 is not None:
                    amd = self.detector.detect_amd_cycle(df_m5)
                    if amd and amd['status'] in ['MANIPULATION_DETECTED', 'MANIPULATION_DOWN', 'MANIPULATION_UP', 'DISTRIBUTION_TREND']:
                        self._execute_smc_for_all_accounts(symbol, df_m5, df_h1, amd)

                # --- ESTRATEGIA 2: Andrea Unger (M30) ---
                df_m30 = base_client.get_rates(symbol, '30m', 100)
                if df_m30 is not None:
                    unger_signal = self.detector.detect_unger_breakout(df_m30)
                    if unger_signal:
                        self._execute_unger_for_all_accounts(symbol, unger_signal)

            except Exception as e:
                logger.error(f"Error analizando {symbol}: {e}")

    def _execute_smc_for_all_accounts(self, symbol, df_m5, df_h1, amd):
        """Lógica original de ejecución SMC."""
        bias = amd['bias']
        latest_price = df_m5['close'].iloc[-1]
        threshold = 0.35
        
        obs_h1 = self.detector.detect_order_blocks(df_h1, displacement_threshold=threshold)
        obs_m5 = self.detector.detect_order_blocks(df_m5, displacement_threshold=threshold)
        all_obs = obs_h1 + obs_m5

        signal_to_notify = None

        if bias == 'BULLISH':
            bullish_obs = [ob for ob in all_obs if ob['type'] == 'BULLISH_OB']
            if bullish_obs:
                ob = bullish_obs[-1]
                if ob['low'] < latest_price and latest_price <= ob['high'] * 1.015:
                    sl = ob['low']
                    risk_val = latest_price - sl
                    tp = latest_price + (risk_val * 2.5)
                    signal_to_notify = ('buy', latest_price, sl, tp, "SMC Institutional")

        elif bias == 'BEARISH':
            bearish_obs = [ob for ob in all_obs if ob['type'] == 'BEARISH_OB']
            if bearish_obs:
                ob = bearish_obs[-1]
                if ob['high'] > latest_price and latest_price >= ob['low'] * 0.985:
                    sl = ob['high']
                    risk_val = sl - latest_price
                    tp = latest_price - (risk_val * 2.5)
                    signal_to_notify = ('sell', latest_price, sl, tp, "SMC Institutional")

        if signal_to_notify:
            self._dispatch_orders(symbol, signal_to_notify)

    def _execute_unger_for_all_accounts(self, symbol, unger_signal):
        """Lógica de ejecución para la estrategia de Andrea Unger."""
        side = unger_signal['side']
        price = unger_signal['price']
        sl = unger_signal['sl']
        tp = unger_signal['tp']
        reason = unger_signal['reason']
        
        signal_to_notify = (side, price, sl, tp, reason)
        self._dispatch_orders(symbol, signal_to_notify)

    def _dispatch_orders(self, symbol, signal_to_notify):
        """Envía las órdenes a todas las cuentas configuradas."""
        side, price, sl, tp, strategy_name = signal_to_notify
        leverage = 5
        
        # Notificar una vez con el nombre de la estrategia
        self.notifier.notify_trade(symbol, side, price, sl, tp, strategy_name=strategy_name)
        logger.info(f"Señal detectada [{strategy_name}]: {symbol} {side} @ {price}")
        
        for acc_data in self.account_clients:
            client = acc_data['client']
            executor = acc_data['executor']
            risk_mgr = acc_data['risk']
            
            try:
                client.set_leverage(symbol, leverage)
                balance = client.get_balance('USDT')
                amount = risk_mgr.calculate_amount(symbol, balance, price, leverage)

                if risk_mgr.validate_trade(symbol, side, price, sl, tp):
                    logger.info(f"Ejecutando {strategy_name} en cuenta {client.api_key[:5]}...")
                    executor.execute_market_order(symbol, side, amount, price, sl, tp)
            except Exception as e:
                logger.error(f"Error ejecutando en cuenta {client.api_key[:5]}: {e}")


    def _calculate_crypto_amount(self, symbol, price):
        # Este método ya no es necesario, se usa self.risk.calculate_amount
        pass
