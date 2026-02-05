import pandas as pd
import logging
from modules.pattern_detector import PatternDetector

logger = logging.getLogger(__name__)

class Backtester:
    """Sistema de Backtesting para estrategias SMC/AMD."""
    
    def __init__(self, initial_balance=1000.0, risk_per_trade=1.0):
        self.balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.detector = PatternDetector()
        self.trades = []

    def run(self, df_m15, df_h1, symbol):
        """Ejecuta el backtest sobre todo el historial disponible."""
        # Aumentamos el rango para analizar todo lo que descargamos (500 velas)
        # Dejamos 60 velas iniciales para tener un rango de Asia válido
        start_idx = 60
        end_idx = len(df_m15)
        
        logger.info(f"Iniciando Backtest Exhaustivo para {symbol} ({end_idx - start_idx} velas M15)...")
        
        for i in range(start_idx, end_idx):
            current_slice_m15 = df_m15.iloc[:i+1]
            # Sincronización precisa por tiempo: Solo velas H1 anteriores o iguales a la vela M15 actual
            current_time = current_slice_m15['time'].iloc[-1]
            current_slice_h1 = df_h1[df_h1['time'] <= current_time]
            
            if current_slice_h1.empty: continue

            # Detectar patrones en este punto del tiempo
            amd = self.detector.detect_amd_cycle(current_slice_m15, debug=(i % 100 == 0))
            
            # Solo actuamos si hay manipulación detectada o distribución
            if amd and amd['status'] in ['MANIPULATION_DETECTED', 'MANIPULATION_DOWN', 'MANIPULATION_UP', 'DISTRIBUTION_TREND']:
                obs = self.detector.detect_order_blocks(current_slice_h1, displacement_threshold=0.35)
                bias = amd['bias']
                price = current_slice_m15['close'].iloc[-1]
                
                # Evitar múltiples entradas para el mismo sesgo si la última fue hace menos de 20 velas
                if self.trades:
                    last_trade = self.trades[-1]
                    time_diff = (current_slice_m15['time'].iloc[-1] - last_trade['time']).total_seconds() / 60
                    if last_trade['symbol'] == symbol and last_trade['side'] == ('BUY' if bias == 'BULLISH' else 'SELL') and time_diff < 300:
                        continue

                if bias == 'BULLISH':
                    # Buscamos OB en H1 O en M15 (más sensible para backtest)
                    bullish_obs_h1 = [ob for ob in obs if ob['type'] == 'BULLISH_OB']
                    obs_m15 = self.detector.detect_order_blocks(current_slice_m15, displacement_threshold=0.35)
                    bullish_obs_m15 = [ob for ob in obs_m15 if ob['type'] == 'BULLISH_OB']
                    
                    all_bullish = bullish_obs_h1 + bullish_obs_m15
                    if not all_bullish:
                        continue
                    
                    ob = all_bullish[-1]
                    # En una compra, el SL debe estar ABAJO del precio
                    # Si el OB está por encima del precio actual, no es una mitigación válida para compra
                    if ob['low'] < price:
                        # Verificación de mitigación: Margen del 1.5% para Crypto
                        if price <= ob['high'] * 1.015:
                            sl = ob['low']
                            risk = price - sl
                            tp = price + (risk * 2.5)
                            self._record_trade(symbol, 'BUY', price, sl, tp, current_slice_m15['time'].iloc[-1])

                elif bias == 'BEARISH':
                    bearish_obs_h1 = [ob for ob in obs if ob['type'] == 'BEARISH_OB']
                    obs_m15 = self.detector.detect_order_blocks(current_slice_m15, displacement_threshold=0.35)
                    bearish_obs_m15 = [ob for ob in obs_m15 if ob['type'] == 'BEARISH_OB']
                    
                    all_bearish = bearish_obs_h1 + bearish_obs_m15
                    if not all_bearish:
                        continue
                        
                    ob = all_bearish[-1]
                    # En una venta, el SL debe estar ARRIBA del precio
                    if ob['high'] > price:
                        # Verificación de mitigación
                        if price >= ob['low'] * 0.985:
                            sl = ob['high']
                            risk = sl - price
                            tp = price - (risk * 2.5)
                            self._record_trade(symbol, 'SELL', price, sl, tp, current_slice_m15['time'].iloc[-1])

        self._print_results(symbol)

    def _record_trade(self, symbol, side, price, sl, tp, timestamp):
        risk = abs(price - sl)
        if risk == 0: return
        
        reward = abs(tp - price)
        
        trade = {
            'symbol': symbol,
            'side': side,
            'entry': price,
            'sl': sl,
            'tp': tp,
            'rr': reward / risk,
            'time': timestamp
        }
        self.trades.append(trade)

    def _print_results(self, symbol):
        if not self.trades:
            print(f"\n--- Backtest {symbol}: Sin operaciones detectadas ---")
            return
            
        print(f"\n--- RESULTADOS DEL BACKTEST ({symbol}) ---")
        for t in self.trades:
            if t['symbol'] == symbol:
                print(f"[{t['time']}] {t['side']} @ {t['entry']:.2f} | SL: {t['sl']:.2f} | TP: {t['tp']:.2f} | R:R: {t['rr']:.2f}")
        
        symbol_trades = [t for t in self.trades if t['symbol'] == symbol]
        print(f"Total Operaciones {symbol}: {len(symbol_trades)}")
        print("-------------------------------\n")
