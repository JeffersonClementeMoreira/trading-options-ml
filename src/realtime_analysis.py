#!/usr/bin/env python3
"""
Análise com dados reais: M15 → Previsão para D+1 14:00 → Múltiplos horários de entrada
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path
from trading_decision import TradingDecisionEngine, format_signal_for_backtest, ACTION_COLOR_MAP, TradeAction


def parse_mt5_date(date_str, time_str):
    """Parse MT5 date/time format (2023.01.01 22:00:00)"""
    date_str = date_str.replace(".", "-")
    datetime_str = f"{date_str} {time_str}"
    return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")


def load_mt5_data(filepath, limit=None):
    """Carrega dados reais do MT5"""
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for i, row in enumerate(reader):
            if limit and i >= limit:
                break
            try:
                dt = parse_mt5_date(row['<DATE>'], row['<TIME>'])
                data.append({
                    'datetime': dt,
                    'open': float(row['<OPEN>']),
                    'high': float(row['<HIGH>']),
                    'low': float(row['<LOW>']),
                    'close': float(row['<CLOSE>']),
                    'volume': int(row['<TICKVOL>']),
                })
            except Exception as e:
                print(f"Erro ao parsear linha: {e}")
                continue
    return data


def aggregate_to_daily(m15_data):
    """Agrupa dados M15 em candles diários (D1)"""
    daily = {}
    
    for candle in m15_data:
        dt = candle['datetime']
        date_key = dt.date()
        
        if date_key not in daily:
            daily[date_key] = {
                'date': date_key,
                'open': candle['open'],
                'high': candle['high'],
                'low': candle['low'],
                'close': candle['close'],
                'volume': candle['volume'],
            }
        else:
            daily[date_key]['high'] = max(daily[date_key]['high'], candle['high'])
            daily[date_key]['low'] = min(daily[date_key]['low'], candle['low'])
            daily[date_key]['close'] = candle['close']
            daily[date_key]['volume'] += candle['volume']
    
    return sorted(daily.values(), key=lambda x: x['date'])


def calculate_rsi(closes, period=14):
    """Calcula RSI (Relative Strength Index)"""
    if len(closes) < period + 1:
        return 50.0  # RSI neutro se dados insuficientes
    
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    seed = sum(deltas[:period]) / period
    
    gains = [max(d, 0) for d in deltas[:period]]
    losses = [-min(d, 0) for d in deltas[:period]]
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    for i in range(period, len(deltas)):
        gain = max(deltas[i], 0)
        loss = -min(deltas[i], 0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
    
    rs = avg_gain / avg_loss if avg_loss != 0 else 100
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_volatility(closes, period=20):
    """Calcula volatilidade histórica (desvio padrão dos retornos)"""
    if len(closes) < period:
        return 0.01
    
    recent_closes = closes[-period:]
    returns = [(recent_closes[i] - recent_closes[i-1]) / recent_closes[i-1] 
               for i in range(1, len(recent_closes))]
    
    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    volatility = variance ** 0.5
    return max(volatility, 0.0001)


def calculate_momentum(closes, period=5):
    """Calcula momentum (mudança percentual nos últimos N períodos)"""
    if len(closes) < period:
        return 0.0
    
    momentum = (closes[-1] - closes[-period]) / closes[-period]
    return momentum


def simulate_xgboost_probabilities_from_features(daily_data, current_index):
    """
    Simula probabilidades XGBoost baseado em features HISTÓRICAS REAIS (SEM DATA LEAKAGE)
    
    VERSÃO MELHORADA: Foca nas features com real poder preditivo
    
    Features usadas (com pesos reais):
    - RSI 14 (🟢 BOM: 55% acurácia) - PESO ALTO
    - Momentum 5d (🟢 BOM: separação clara) - PESO ALTO
    - Volatilidade (⚠️  FRACO: só usa como filtro)
    - Volume Ratio (⚠️  FRACO: só usa como filtro)
    - Posição no Range (⚠️  FRACO: só usa como filtro)
    
    Args:
        daily_data: Lista com todos os candles diários até agora
        current_index: Índice do dia atual (não inclui futuros)
    
    Returns:
        (p_up, p_down, p_flat) - Probabilidades baseadas em features BOAS
    """
    if current_index < 20:
        # Se poucos dados, retornar probabilidade neutra
        return 0.33, 0.33, 0.34
    
    current_day = daily_data[current_index]
    
    # Extrair histórico até o dia atual (SEM incluir próximo dia)
    historical_closes = [d['close'] for d in daily_data[:current_index + 1]]
    historical_highs = [d['high'] for d in daily_data[:current_index + 1]]
    historical_lows = [d['low'] for d in daily_data[:current_index + 1]]
    historical_volumes = [d['volume'] for d in daily_data[:current_index + 1]]
    
    # Calcular features
    rsi = calculate_rsi(historical_closes, period=14)
    volatility = calculate_volatility(historical_closes, period=20)
    momentum = calculate_momentum(historical_closes, period=5)
    
    # Volume relativo
    avg_volume = sum(historical_volumes[-20:]) / 20 if len(historical_volumes) >= 20 else current_day['volume']
    volume_ratio = current_day['volume'] / avg_volume if avg_volume > 0 else 1.0
    
    # Posição no range
    recent_highs = historical_highs[-20:]
    recent_lows = historical_lows[-20:]
    highest = max(recent_highs)
    lowest = min(recent_lows)
    range_size = highest - lowest
    
    if range_size > 0:
        position = (current_day['close'] - lowest) / range_size
    else:
        position = 0.5
    
    # ===== LÓGICA SIMPLIFICADA (Focando em Features Boas) =====
    
    # Começar NEUTRO
    p_up = 0.5
    p_down = 0.5
    p_flat = 0.0  # Inicialmente não há incerteza
    
    # ========== AJUSTE 1: RSI (FEATURE BOA - 55% acurácia) ==========
    # RSI > 50 tende a UP, RSI < 50 tende a DOWN
    # Usar mais agresivamente pois tem real poder preditivo
    
    if rsi > 65:  # Sobrecompra = tendência UP confirmada
        p_up += 0.25
        p_down -= 0.15
    elif rsi > 55:  # Levemente alto = leve tendência UP
        p_up += 0.12
        p_down -= 0.08
    elif rsi > 50:  # Acima de neutro
        p_up += 0.06
        p_down -= 0.03
    elif rsi < 35:  # Sobrevenda = tendência DOWN confirmada
        p_down += 0.25
        p_up -= 0.15
    elif rsi < 45:  # Levemente baixo = leve tendência DOWN
        p_down += 0.12
        p_up -= 0.08
    elif rsi < 50:  # Abaixo de neutro
        p_down += 0.06
        p_up -= 0.03
    
    # ========== AJUSTE 2: MOMENTUM (FEATURE BOA - forte separação) ==========
    # Momentum positivo = já está subindo (reforça tendência)
    # Momentum negativo = já está caindo (reforça tendência)
    
    if momentum > 0.015:  # +1.5% em 5 dias = forte UP
        p_up += 0.20
        p_down -= 0.12
    elif momentum > 0.008:  # +0.8% em 5 dias = moderado UP
        p_up += 0.12
        p_down -= 0.06
    elif momentum > 0.003:  # +0.3% em 5 dias = leve UP
        p_up += 0.06
        p_down -= 0.03
    elif momentum < -0.015:  # -1.5% em 5 dias = forte DOWN
        p_down += 0.20
        p_up -= 0.12
    elif momentum < -0.008:  # -0.8% em 5 dias = moderado DOWN
        p_down += 0.12
        p_up -= 0.06
    elif momentum < -0.003:  # -0.3% em 5 dias = leve DOWN
        p_down += 0.06
        p_up -= 0.03
    
    # ========== AJUSTE 3: VOLATILIDADE (FEATURE FRACA - usar só como filtro) ==========
    # Volatilidade alta = mais incerteza
    # Volatilidade baixa = menos movimento esperado
    
    if volatility > 0.020:
        # Muita volatilidade = incerteza (reduz confiança)
        p_flat = 0.15
        p_up = (p_up - 0.075) / (1 - p_flat)
        p_down = (p_down - 0.075) / (1 - p_flat)
    elif volatility < 0.005:
        # Muito pouca volatilidade = consolidação (também é incerteza)
        p_flat = 0.10
        p_up = (p_up - 0.05) / (1 - p_flat)
        p_down = (p_down - 0.05) / (1 - p_flat)
    
    # ========== AJUSTE 4: VOLUME (FEATURE FRACA - usar só como filtro) ==========
    # Volume muito alto com momentum = reforça sinal
    # Volume muito baixo = qualquer movimento é questionável
    
    if volume_ratio > 2.0 and abs(momentum) > 0.005:
        # Alto volume + momentum claro = reforça
        p_up = p_up * 1.1 if momentum > 0 else p_up * 0.9
        p_down = p_down * 1.1 if momentum < 0 else p_down * 0.9
    elif volume_ratio < 0.3:
        # Volume muito baixo = reduz confiança
        p_flat = 0.10
        p_up = (p_up - 0.05) / (1 - p_flat)
        p_down = (p_down - 0.05) / (1 - p_flat)
    
    # ========== NORMALIZAR ==========
    total = p_up + p_down + p_flat
    
    # Garantir que as probabilidades são válidas e somam 1.0
    if total > 0:
        p_up = p_up / total
        p_down = p_down / total
        p_flat = p_flat / total
    else:
        p_up = 0.33
        p_down = 0.33
        p_flat = 0.34
    
    # Garantir valores mínimos (pelo menos 5% cada)
    p_up = max(0.05, min(0.90, p_up))
    p_down = max(0.05, min(0.90, p_down))
    p_flat = 1.0 - p_up - p_down
    
    return p_up, p_down, p_flat


def create_signals_with_entry_times(daily_data, entry_times=None):
    """
    Cria sinais com múltiplos horários de entrada
    
    Args:
        daily_data: Dados diários agregados
        entry_times: Lista de horas para entrada (ex: [18, 19, 20])
    
    Returns:
        Lista de sinais com estrutura: data_atual, hora_entrada, prediction_date, ..., action
    """
    if entry_times is None:
        entry_times = [18, 19, 20]
    
    engine = TradingDecisionEngine(
        confidence_threshold=0.40,
        strangle_threshold=0.40,
    )
    
    signals = []
    
    for i in range(len(daily_data) - 1):
        current_day = daily_data[i]
        next_day = daily_data[i + 1]
        
        # ✅ CORRIGIDO: Usar features HISTÓRICAS (sem dados futuros)
        p_up, p_down, p_flat = simulate_xgboost_probabilities_from_features(
            daily_data, 
            i  # Índice atual (não próximo)
        )
        
        # Previsão é SEMPRE para o próximo dia às 14:00
        prediction_date = next_day['date']
        prediction_datetime = f"{prediction_date} 14:00:00"
        
        # Criar sinal baseado na previsão
        signal = engine.decide(
            symbol="EURUSD",
            timeframe="D1",
            datetime_str=prediction_datetime,
            p_down=p_down,
            p_flat=p_flat,
            p_up=p_up,
        )
        signal_dict = format_signal_for_backtest(signal)
        
        # Múltiplos horários de entrada no dia anterior
        for entry_hour in entry_times:
            entry_datetime = datetime.combine(current_day['date'], __import__('datetime').time(entry_hour, 0))
            
            row = {
                # Data e hora atual
                'current_date': current_day['date'],
                'current_close': f"{current_day['close']:.5f}",
                'current_volume': current_day['volume'],
                
                # Horário de entrada (quando abrir a ordem)
                'entry_time': f"{entry_hour}:00:00",
                'entry_datetime': entry_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                
                # Alvo da previsão (sempre D+1 14:00)
                'prediction_date': prediction_date,
                'prediction_time': "14:00:00",
                'prediction_datetime': prediction_datetime,
                
                # ADICIONADO: Preço do próximo dia (SÓ PARA VALIDAÇÃO)
                'next_day_close': f"{next_day['close']:.5f}",
                'price_movement': f"{((next_day['close'] - current_day['close']) / current_day['close'] * 100):.2f}%",
                'actual_direction': "UP" if next_day['close'] > current_day['close'] else "DOWN",
                
                # Probabilidades e ação
                'p_up': f"{signal.p_up:.4f}",
                'p_down': f"{signal.p_down:.4f}",
                'p_flat': f"{signal.p_flat:.4f}",
                'action': signal.action.value,
                'confidence': f"{signal.confidence:.4f}",
            }
            signals.append(row)
    
    return signals


def save_analysis_csv(signals, output_path):
    """Salva análise em CSV"""
    if not signals:
        print("❌ Nenhum sinal para salvar")
        return
    
    fieldnames = list(signals[0].keys())
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(signals)
    
    print(f"✅ Análise salva em: {output_path}")
    print(f"   Total de linhas: {len(signals)}")


def analyze_entry_times(signals):
    """Analisa qual horário de entrada teve melhor desempenho"""
    stats = {}
    
    for signal in signals:
        entry_time = signal['entry_time']
        action = signal['action']
        
        if entry_time not in stats:
            stats[entry_time] = {
                'total': 0,
                'call_sell': 0,
                'put_sell': 0,
                'strangle': 0,
                'no_trade': 0,
            }
        
        stats[entry_time]['total'] += 1
        stats[entry_time][action.lower().replace('-', '_')] += 1
    
    print("\n" + "="*70)
    print("📊 ANÁLISE POR HORÁRIO DE ENTRADA")
    print("="*70)
    
    for entry_time in sorted(stats.keys()):
        data = stats[entry_time]
        print(f"\n🕐 Horário {entry_time}:")
        print(f"   Total: {data['total']} sinais")
        print(f"   • CALL_SELL:  {data['call_sell']:4d} ({100*data['call_sell']/data['total']:.1f}%)")
        print(f"   • PUT_SELL:   {data['put_sell']:4d} ({100*data['put_sell']/data['total']:.1f}%)")
        print(f"   • STRANGLE:   {data['strangle']:4d} ({100*data['strangle']/data['total']:.1f}%)")
        print(f"   • NO_TRADE:   {data['no_trade']:4d} ({100*data['no_trade']/data['total']:.1f}%)")


if __name__ == "__main__":
    print("="*70)
    print("🔍 ANÁLISE COM DADOS REAIS: EUR/USD M15")
    print("="*70)
    
    # Carregar dados
    print("\n📥 Carregando dados...")
    mt5_data = load_mt5_data('dados/EURUSD_M15_202301012200_202605222015.csv', limit=10000)
    print(f"   ✅ {len(mt5_data)} candles M15 carregados")
    
    # Agregar para diário
    print("\n📊 Agregando para D1...")
    daily_data = aggregate_to_daily(mt5_data)
    print(f"   ✅ {len(daily_data)} dias agregados")
    
    # Criar sinais com múltiplos horários
    print("\n🎯 Criando sinais com múltiplos horários de entrada...")
    signals = create_signals_with_entry_times(daily_data, entry_times=[18, 19, 20])
    print(f"   ✅ {len(signals)} sinais criados")
    
    # Salvar
    output_path = "predictions/realtime_analysis.csv"
    Path("predictions").mkdir(exist_ok=True)
    save_analysis_csv(signals, output_path)
    
    # Análise
    analyze_entry_times(signals)
    
    print("\n" + "="*70)
    print("✅ Análise completa!")
    print("="*70)
