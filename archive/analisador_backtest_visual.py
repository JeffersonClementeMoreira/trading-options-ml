#!/usr/bin/env python3
"""
Analisador Visual do Backtest Detalhado

Mostra OHLC + Indicadores + XGBoost em formato fácil de ler
"""

import pandas as pd
import sys

def analisar_backtest_visual(csv_path: str):
    """Mostra análise visual do backtest."""
    
    df = pd.read_csv(csv_path)
    
    print("\n" + "="*150)
    print("🎯 ANÁLISE VISUAL DO BACKTEST - DETALHES COMPLETOS")
    print("="*150 + "\n")
    
    # Filtrar trades com resultado
    df_valid = df[df['result'].isin(['UP', 'DOWN'])].copy()
    
    for idx, row in df_valid.iterrows():
        date = row['date']
        day = row['day_of_week']
        
        # Status
        status = row['acertou']
        if status == '✅':
            emoji = "✅ ACERTOU"
            status_color = "VENCEDOR"
        else:
            emoji = "❌ ERROU"
            status_color = "PERDEDOR"
        
        print(f"\n{emoji} | {date} ({day})")
        print(f"{'─'*150}")
        
        # OHLC
        print(f"📊 OHLC DO DIA:")
        print(f"   Open:  {row['open']:8.5f} | High: {row['high']:8.5f} | Low: {row['low']:8.5f} | Close: {row['close']:8.5f}")
        print(f"   Range: {row['range_pct']:6.2f}% | Volume: {int(row['volume']):,}")
        
        # Indicadores
        print(f"\n📈 INDICADORES TÉCNICOS:")
        sma20 = f"{row['sma20']:.5f}" if pd.notna(row['sma20']) else "N/A"
        sma50 = f"{row['sma50']:.5f}" if pd.notna(row['sma50']) else "N/A"
        sma200 = f"{row['sma200']:.5f}" if pd.notna(row['sma200']) else "N/A"
        rsi14 = f"{row['rsi14']:.1f}" if pd.notna(row['rsi14']) else "N/A"
        macd = f"{row['macd']:.6f}" if pd.notna(row['macd']) else "N/A"
        volatility = f"{row['volatility']:.4f}%" if pd.notna(row['volatility']) else "N/A"
        momentum = f"{row['momentum10']:+.2f}%" if pd.notna(row['momentum10']) else "N/A"
        
        print(f"   SMA20:        {sma20}")
        print(f"   SMA50:        {sma50}")
        print(f"   SMA200:       {sma200}")
        print(f"   RSI(14):      {rsi14}")
        print(f"   MACD:         {macd}")
        print(f"   Volatilidade: {volatility}")
        print(f"   Momentum(10): {momentum}")
        
        # Confluência
        print(f"\n🎯 CONFLUÊNCIA DE TIMEFRAMES:")
        m15_trend = row['m15_trend']
        h4_trend = row['h4_trend']
        is_aligned = row['is_aligned']
        alignment_score = row['alignment_score']
        
        print(f"   M15 Trend:    {m15_trend}")
        print(f"   H4 Trend:     {h4_trend}")
        print(f"   Alinhados?    {is_aligned} (Score: {alignment_score:.0%})")
        
        # XGBoost
        print(f"\n🤖 PREDIÇÃO XGBOOST:")
        xgb_pred = row['xgb_pred']
        xgb_conf = row['xgb_confidence']
        print(f"   Sinal:        {xgb_pred}")
        print(f"   Confiança:    {xgb_conf:.1%}")
        
        # Resultado
        print(f"\n📈 RESULTADO REAL:")
        result = row['result']
        next_close = row['next_close']
        change_pct = row['change_pct']
        
        print(f"   Fechamento próx dia: {next_close:.5f}")
        print(f"   Resultado: {result} ({change_pct:+.2f}%)")
        
        # Análise
        print(f"\n💡 ANÁLISE:")
        if xgb_pred == "BUY":
            expected = "Esperado: Subida ⬆️"
        else:
            expected = "Esperado: Queda ⬇️"
        
        if result == "UP":
            actual = "Resultado: Subiu ⬆️"
        else:
            actual = "Resultado: Caiu ⬇️"
        
        print(f"   {expected}")
        print(f"   {actual}")
        
        if status == "✅ ACERTOU":
            print(f"   → {xgb_pred} foi correto! Movimento {change_pct:+.2f}%")
            if xgb_conf > 0.8:
                print(f"   → Modelo tinha alta confiança ({xgb_conf:.0%})")
            else:
                print(f"   → Modelo tinha média confiança ({xgb_conf:.0%})")
        else:
            print(f"   → {xgb_pred} estava errado. Movimento foi oposto!")
            if xgb_conf > 0.85:
                print(f"   → Modelo estava MUITO confiante mas errou ({xgb_conf:.0%})")
            elif xgb_conf > 0.7:
                print(f"   → Modelo estava confiante mas errou ({xgb_conf:.0%})")
        
        if is_aligned == "✅":
            print(f"   → Confluência confirma: M15 e H4 alinhados ✅")
        else:
            print(f"   → SEM confluência: M15 e H4 divergentes ⚠️")
        
        print()
    
    # Resumo
    print("\n" + "="*150)
    print("📊 RESUMO GERAL")
    print("="*150 + "\n")
    
    total = len(df_valid)
    acertos = len(df_valid[df_valid['acertou'] == '✅'])
    erros = len(df_valid[df_valid['acertou'] == '❌'])
    win_rate = acertos / total * 100
    
    print(f"Total de trades: {total}")
    print(f"Acertos:         {acertos} ({win_rate:.1f}%)")
    print(f"Erros:           {erros} ({100-win_rate:.1f}%)")
    
    # Com confluência
    aligned = df_valid[df_valid['is_aligned'] == '✅']
    if len(aligned) > 0:
        aligned_correct = len(aligned[aligned['acertou'] == '✅'])
        aligned_wr = aligned_correct / len(aligned) * 100
        print(f"\nCom confluência:    {aligned_correct}/{len(aligned)} acertos ({aligned_wr:.1f}%)")
    
    # Sem confluência
    divergent = df_valid[df_valid['is_aligned'] == '❌']
    if len(divergent) > 0:
        divergent_correct = len(divergent[divergent['acertou'] == '✅'])
        divergent_wr = divergent_correct / len(divergent) * 100
        print(f"Sem confluência:    {divergent_correct}/{len(divergent)} acertos ({divergent_wr:.1f}%)")
    
    # Confiança média
    avg_conf_win = df_valid[df_valid['acertou'] == '✅']['xgb_confidence'].mean() if len(df_valid[df_valid['acertou'] == '✅']) > 0 else 0
    avg_conf_loss = df_valid[df_valid['acertou'] == '❌']['xgb_confidence'].mean() if len(df_valid[df_valid['acertou'] == '❌']) > 0 else 0
    
    print(f"\nConfiança média (acertos):  {avg_conf_win:.1%}")
    print(f"Confiança média (erros):    {avg_conf_loss:.1%}")
    
    print("\n" + "="*150)
    print("✨ INSIGHTS PARA VOCÊ ANALISAR MANUALMENTE:")
    print("="*150 + "\n")
    
    print("1. PADRÕES NOS VENCEDORES:")
    print("   → Qual RSI tinha nos trades que acertou?")
    print("   → Qual SMA tinha? Preço acima ou abaixo de MA200?")
    print("   → Qual confiança do XGBoost tinha?")
    
    print("\n2. PADRÕES NOS PERDEDORES:")
    print("   → Qual era o padrão técnico?")
    print("   → O XGBoost estava confiante? Devemos ignorar altas confianças em certos cenários?")
    print("   → Havia confluência? Há diferença?")
    
    print("\n3. MELHORIAS POSSÍVEIS:")
    print("   → Filtrar por confiança mínima (ex: 80%)?")
    print("   → Usar apenas trades com confluência?")
    print("   → Ajustar stop loss baseado em range?")
    print("   → Aguardar RSI em zona específica?")
    
    print()


if __name__ == '__main__':
    # Usar último arquivo gerado
    import glob
    files = glob.glob('backtest_results/backtest_detalhado_*.csv')
    if files:
        latest_file = sorted(files)[-1]
        print(f"📂 Analisando: {latest_file}\n")
        analisar_backtest_visual(latest_file)
    else:
        print("❌ Nenhum backtest detalhado encontrado")

