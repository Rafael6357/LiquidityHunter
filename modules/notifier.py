import requests
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Clase para enviar notificaciones a Telegram."""
    
    def __init__(self):
        load_dotenv()
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        # Soportar múltiples IDs separados por coma
        self.chat_ids = os.getenv("TELEGRAM_CHAT_ID", "").split(",")
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_message(self, message):
        """Envía un mensaje de texto a todos los destinatarios configurados."""
        if not self.token or not self.chat_ids:
            logger.warning("Telegram no configurado. Token o Chat IDs faltantes.")
            return False
            
        success = True
        for chat_id in self.chat_ids:
            chat_id = chat_id.strip()
            if not chat_id: continue
            
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            try:
                response = requests.post(self.base_url, data=payload)
                if response.status_code != 200:
                    logger.error(f"Error enviando a Telegram ({chat_id}): {response.text}")
                    success = False
            except Exception as e:
                logger.error(f"Excepción al enviar a Telegram ({chat_id}): {e}")
                success = False
        return success

    def notify_trade(self, symbol, side, price, sl, tp):
        """Notifica una nueva operación ejecutada."""
        header = "NUEVA OPERACION INSTITUCIONAL"
        msg = (
            f"*{header}*\n\n"
            f"*Simbolo:* {symbol}\n"
            f"*Accion:* {side.upper()}\n"
            f"*Precio Entrada:* {price:.4f}\n"
            f"*Stop Loss:* {sl:.4f}\n"
            f"*Take Profit:* {tp:.4f}\n\n"
            f"Liquidity Hunter v3.0"
        )
        return self.send_message(msg)

    def send_welcome(self):
        """Envía un mensaje de bienvenida para verificar la conexión."""
        msg = (
            "*LIQUIDITY HUNTER v3.0 CONECTADO*\n\n"
            "El bot institucional está operativo y monitoreando:\n"
            "• BTC/USDT\n"
            "• ETH/USDT\n"
            "• SOL/USDT\n\n"
            "_Esperando huellas institucionales..._"
        )
        return self.send_message(msg)
