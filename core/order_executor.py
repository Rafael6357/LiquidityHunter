import logging

logger = logging.getLogger(__name__)

class OrderExecutor:
    """Ejecutor de órdenes para CoinEx."""

    def __init__(self, coinex_client):
        self.client = coinex_client
        self.exchange = coinex_client.exchange

    def execute_market_order(self, symbol, side, amount, price=None, sl=None, tp=None):
        """Ejecuta una orden de mercado en Futuros con SL y TP opcionales."""
        try:
            logger.info(f"Ejecutando {side} Market en FUTUROS {symbol} | Cantidad: {amount}")
            
            # 1. Configurar margen cruzado y apalancamiento antes de operar (si es necesario)
            # Nota: Esto se suele hacer una vez, pero lo ponemos aquí por seguridad
            
            # 2. Ejecutar orden principal
            # En CCXT para futuros, 'amount' suele ser la cantidad en la moneda base (ej: 0.001 BTC)
            order = self.exchange.create_order(symbol, 'market', side, amount)
            logger.info(f"Orden de futuros ejecutada: {order['id']}")

            # 3. Configurar SL/TP mediante órdenes de cierre (reduce-only)
            if sl:
                sl_side = 'sell' if side == 'buy' else 'buy'
                # En futuros usamos stop-market para mayor seguridad en el cierre
                self.exchange.create_order(symbol, 'stop_market', sl_side, amount, None, {
                    'stopPrice': sl,
                    'reduceOnly': True
                })
                logger.info(f"Stop Loss de futuros configurado en {sl}")
            
            if tp:
                tp_side = 'sell' if side == 'buy' else 'buy'
                # Take Profit como orden limit con reduceOnly
                self.exchange.create_order(symbol, 'limit', tp_side, amount, tp, {
                    'reduceOnly': True
                })
                logger.info(f"Take Profit de futuros configurado en {tp}")

            return order
        except Exception as e:
            logger.error(f"Error al ejecutar orden de futuros en CoinEx: {e}")
            return None
