import pandas as pd

class PatternDetector:
    """Clase encargada de detectar patrones institucionales (SMC)."""

    @staticmethod
    def detect_order_blocks(df, displacement_threshold=0.5):
        """
        Detecta Order Blocks con un umbral de desplazamiento personalizable.
        Reducido a 0.5 para capturar más zonas institucionales en temporalidades altas.
        """
        obs = []
        for i in range(2, len(df) - 1):
            body_size = abs(df['close'].iloc[i] - df['open'].iloc[i])
            full_range = df['high'].iloc[i] - df['low'].iloc[i]
            
            # Movimiento fuerte (Displacement)
            if full_range > 0 and (body_size / full_range) > displacement_threshold:
                # Bullish OB: Vela fuerte alcista después de vela bajista
                if df['close'].iloc[i] > df['open'].iloc[i] and df['close'].iloc[i-1] < df['open'].iloc[i-1]:
                    obs.append({
                        'type': 'BULLISH_OB', 
                        'price': df['low'].iloc[i-1], 
                        'time': df['time'].iloc[i-1],
                        'high': df['high'].iloc[i-1],
                        'low': df['low'].iloc[i-1]
                    })
                
                # Bearish OB: Vela fuerte bajista después de vela alcista
                elif df['close'].iloc[i] < df['open'].iloc[i] and df['close'].iloc[i-1] > df['open'].iloc[i-1]:
                    obs.append({
                        'type': 'BEARISH_OB', 
                        'price': df['high'].iloc[i-1], 
                        'time': df['time'].iloc[i-1],
                        'high': df['high'].iloc[i-1],
                        'low': df['low'].iloc[i-1]
                    })
        return obs

    @staticmethod
    def detect_liquidity_sweeps(df, lookback=20):
        """Detecta barridos de liquidez (mechas que rompen máximos/mínimos previos)."""
        sweeps = []
        for i in range(lookback, len(df)):
            window = df.iloc[i-lookback:i]
            prev_high = window['high'].max()
            prev_low = window['low'].min()
            
            curr_high = df['high'].iloc[i]
            curr_low = df['low'].iloc[i]
            curr_close = df['close'].iloc[i]
            
            if curr_high > prev_high and curr_close < prev_high:
                sweeps.append({'type': 'BUY_SIDE_SWEEP', 'price': curr_high, 'time': df['time'].iloc[i]})
            
            if curr_low < prev_low and curr_close > prev_low:
                sweeps.append({'type': 'SELL_SIDE_SWEEP', 'price': curr_low, 'time': df['time'].iloc[i]})
        return sweeps

    @staticmethod
    def detect_unger_breakout(df_m30):
        """
        Implementa la lógica de Breakout de Andrea Unger (VBO).
        Identifica un rango inicial (00:00 - 06:00 UTC) y busca rupturas con filtro de tendencia.
        """
        if df_m30 is None or len(df_m30) < 50:
            return None

        # 1. Definir el rango del día actual (00:00 - 06:00 UTC)
        now = df_m30['time'].iloc[-1]
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        range_end = now.replace(hour=6, minute=0, second=0, microsecond=0)

        day_range_df = df_m30[(df_m30['time'] >= today_start) & (df_m30['time'] <= range_end)]
        
        if day_range_df.empty:
            # Si no hay datos de hoy todavía, usar las primeras 12 velas de 30m (6 horas)
            day_range_df = df_m30.iloc[:12]

        range_high = day_range_df['high'].max()
        range_low = day_range_df['low'].min()

        # 2. Filtro de Tendencia (SMA 50)
        df_m30['sma50'] = df_m30['close'].rolling(window=50).mean()
        latest_sma = df_m30['sma50'].iloc[-1]
        curr_close = df_m30['close'].iloc[-1]

        # 3. Cálculo de ATR para Stop Loss
        df_m30['tr'] = pd.concat([
            df_m30['high'] - df_m30['low'],
            (df_m30['high'] - df_m30['close'].shift(1)).abs(),
            (df_m30['low'] - df_m30['close'].shift(1)).abs()
        ], axis=1).max(axis=1)
        atr = df_m30['tr'].rolling(window=14).mean().iloc[-1]

        # 4. Lógica de Señal
        # Solo operar después del rango (después de las 06:00 UTC)
        if now <= range_end:
            return None

        signal = None
        if curr_close > range_high and curr_close > latest_sma:
            signal = {
                'side': 'buy',
                'price': curr_close,
                'sl': curr_close - (1.5 * atr),
                'tp': curr_close + (3.0 * atr), # RR 1:2
                'reason': 'Unger Breakout High + SMA50'
            }
        elif curr_close < range_low and curr_close < latest_sma:
            signal = {
                'side': 'sell',
                'price': curr_close,
                'sl': curr_close + (1.5 * atr),
                'tp': curr_close - (3.0 * atr),
                'reason': 'Unger Breakout Low + SMA50'
            }

        return signal

    @staticmethod
    def detect_amd_cycle(df_m15, debug=False):
        """
        Detecta el ciclo AMD basado en sesiones.
        Versión ultra-flexible: Si no hay manipulación de sesión, busca desviaciones de rango dinámico.
        """
        if df_m15 is None or len(df_m15) < 50:
            return None

        # 1. Intentar Sesión de Asia (22:00 - 08:00 UTC)
        asia = df_m15[(df_m15['time'].dt.hour >= 22) | (df_m15['time'].dt.hour < 8)]
        
        if not asia.empty:
            asia_high, asia_low = asia['high'].max(), asia['low'].min()
        else:
            # Si no hay datos de Asia (ej. primer inicio), usar un rango de 40 velas como base
            base_range = df_m15.iloc[-60:-20]
            asia_high, asia_low = base_range['high'].max(), base_range['low'].min()

        # 2. Análisis de precio actual (Últimas 10 velas / 2.5 horas)
        recent = df_m15.iloc[-10:]
        curr_high = recent['high'].max()
        curr_low = recent['low'].min()
        curr_close = df_m15['close'].iloc[-1]

        # 3. Detección de Ciclo AMD
        # ACCUMULATION: Precio dentro del rango de Asia
        # MANIPULATION: Precio rompe el rango (Sweep)
        # DISTRIBUTION: El movimiento real tras el sweep
        
        bias = 'NEUTRAL'
        status = 'ACCUMULATION'

        # Umbral de "barrido" (0.1% del precio para Crypto)
        sweep_threshold = curr_close * 0.001 

        # 1. Detección de MANIPULACIÓN (Sweep)
        # Si el precio ha salido del rango, ya es manipulación o expansión
        if curr_high > (asia_high + sweep_threshold):
            status = 'MANIPULATION_UP'
            bias = 'BEARISH' # Buscamos ventas tras el barrido superior
            # Si ya regresó al rango, es una señal más fuerte
            if curr_close < asia_high:
                status = 'MANIPULATION_DETECTED'
        
        elif curr_low < (asia_low - sweep_threshold):
            status = 'MANIPULATION_DOWN'
            bias = 'BULLISH' # Buscamos compras tras el barrido inferior
            # Si ya regresó al rango, es una señal más fuerte
            if curr_close > asia_low:
                status = 'MANIPULATION_DETECTED'
        
        # 2. Si el precio está muy lejos del rango y no regresa, es una expansión/tendencia
        if status in ['MANIPULATION_UP', 'MANIPULATION_DOWN']:
            distance_pct = abs(curr_close - (asia_high if bias == 'BEARISH' else asia_low)) / curr_close
            if distance_pct > 0.05: # Aumentado a 5% para Crypto
                status = 'DISTRIBUTION_TREND'

        # Log para debug interno (solo si se solicita para no saturar la consola)
        if debug:
            print(f"--- Debug AMD --- Range: {asia_low:.2f}-{asia_high:.2f} | Close: {curr_close:.2f} | Status: {status}")

        return {
            'status': status,
            'bias': bias,
            'asia_high': asia_high,
            'asia_low': asia_low
        }
