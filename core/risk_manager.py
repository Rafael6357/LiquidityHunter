import logging

logger = logging.getLogger(__name__)

class RiskManager:
    """Gestiona el riesgo, cálculo de cantidad y validación de órdenes para Crypto."""

    def __init__(self, risk_per_trade=1.0):
        self.risk_per_trade = risk_per_trade

    def calculate_amount(self, symbol, balance, price, leverage=5):
        """
        Calcula la cantidad (amount) de crypto a operar basado en el riesgo y apalancamiento.
        risk_per_trade: Porcentaje del balance total a arriesgar por operación (Capital en riesgo).
        """
        if balance <= 0:
            logger.warning(f"Balance insuficiente para {symbol}")
            return 0.0

        # El riesgo se aplica sobre el balance total (1%)
        # El apalancamiento nos permite controlar una posición más grande con menos margen.
        # Cantidad Nominal = (Balance * Riesgo%) * Apalancamiento / Precio
        risk_amount_usdt = balance * (self.risk_per_trade / 100)
        nominal_amount_usdt = risk_amount_usdt * leverage
        amount = nominal_amount_usdt / price
        
        return amount

    def validate_trade(self, symbol, side, price, sl, tp):
        """Valida si una operación cumple con los requisitos de seguridad."""
        if not sl or not tp:
            logger.warning(f"Operación rechazada: SL o TP no definidos para {symbol}")
            return False
        
        # Verificar relación Riesgo:Beneficio mínima (ej: 1:2)
        risk = abs(price - sl)
        reward = abs(tp - price)
        
        if risk == 0:
            return False
            
        if reward < risk:
            logger.warning(f"Operación rechazada: Ratio R:B insuficiente en {symbol} (R:{risk:.4f}, B:{reward:.4f})")
            return False

        return True
