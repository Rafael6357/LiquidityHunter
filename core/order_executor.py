import logging

logger = logging.getLogger(__name__)

class OrderExecutor:
    """Ejecutor de órdenes para CoinEx."""

    def __init__(self, coinex_client):
        self.client = coinex_client
        self.exchange = coinex_client.exchange

    def execute_market_order(self, symbol, side, amount, price=None, sl=None, tp=None):
        """Ejecuta una orden de mercado con SL y TP opcionales."""
        try:
            logger.info(f"Ejecutando {side} Market en {symbol} | Cantidad/Costo: {amount}")
            
            # 1. Ejecutar orden principal
            # Para CoinEx Market Buy: 'amount' es el costo total en USDT si 'createMarketBuyOrderRequiresPrice' es False
            # Para Market Sell: 'amount' es la cantidad de crypto.
            order = self.exchange.create_order(symbol, 'market', side, amount, price)
            logger.info(f"Orden ejecutada: {order['id']}")

            # 2. Configurar SL/TP (Si el exchange lo soporta vía API o mediante órdenes condicionales)
            # CoinEx en CCXT suele requerir órdenes separadas para SL/TP
            if sl:
                sl_side = 'sell' if side == 'buy' else 'buy'
                self.exchange.create_order(symbol, 'limit', sl_side, amount, sl, {'stopPrice': sl, 'type': 'stop-limit'})
                logger.info(f"Stop Loss configurado en {sl}")
            
            if tp:
                tp_side = 'sell' if side == 'buy' else 'buy'
                self.exchange.create_order(symbol, 'limit', tp_side, amount, tp)
                logger.info(f"Take Profit configurado en {tp}")

            return order
        except Exception as e:
            logger.error(f"Error al ejecutar orden en CoinEx: {e}")
            return None
