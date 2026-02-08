import os
from dotenv import load_dotenv
from core.coinex_client import CoinExClient

def test():
    # Cargar el archivo .env
    load_dotenv()
    accounts = []
    
    # 1. Intentar cargar cuenta principal
    main_key = os.getenv("COINEX_API_KEY")
    main_secret = os.getenv("COINEX_SECRET")
    if main_key and main_secret:
        accounts.append(('Principal', main_key.strip(), main_secret.strip()))
    
    # 2. Intentar cargar cuentas adicionales
    extra = os.getenv("COINEX_EXTRA_ACCOUNTS", "")
    if extra:
        for acc in extra.split(","):
            if ":" in acc:
                parts = acc.split(":")
                if len(parts) == 2:
                    k, s = parts
                    accounts.append(('Extra', k.strip(), s.strip()))

    if not accounts:
        print("\n❌ No se encontraron cuentas configuradas en el archivo .env")
        print("Revisa que COINEX_API_KEY o COINEX_EXTRA_ACCOUNTS tengan datos.")
        return

    print(f"\n--- Verificando {len(accounts)} cuentas en CoinEx Futuros ---")
    for name, k, s in accounts:
        try:
            # Inicializar cliente
            client = CoinExClient(k, s)
            # Intentar obtener balance de USDT en la cuenta de Futuros (Swap)
            balance = client.get_balance('USDT')
            print(f"✅ Cuenta {name} ({k[:6]}...): CONECTADA")
            print(f"   💰 Balance USDT Futuros: {balance:.4f}")
        except Exception as e:
            print(f"❌ Cuenta {name} ({k[:6]}...): ERROR")
            print(f"   ⚠️ Detalle: {e}")

if __name__ == "__main__":
    test()
