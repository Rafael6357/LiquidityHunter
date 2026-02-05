import logging

logger = logging.getLogger(__name__)

class RiskManager:
    """Gestiona el riesgo, cálculo de cantidad y validación de órdenes para Crypto."""

    def __init__(self, risk_per_trade=1.0):
        self.risk_per_trade = risk_per_trade

    def calculate_amount(self, symbol, balance, price):
        """
        Calcula la cantidad (amount) de crypto a operar basado en el riesgo.
        risk_per_trade: Porcentaje del balance total a arriesgar por operación.
        """
        if balance <= 0:
            logger.warning(f"Balance insuficiente para {symbol}")
            return 0.0

        risk_amount_usdt = balance * (self.risk_per_trade / 100)
        amount = risk_amount_usdt / price
        
        # En una versión más avanzada, ajustaríamos según la precisión del símbolo (lot_precision)
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
