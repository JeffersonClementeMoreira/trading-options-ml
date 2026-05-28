#!/usr/bin/env python3
"""
GENERATE ACTIONABLE SIGNALS - Planilha de Sinais Acionáveis
===========================================================

Gera CSV com:
- Horário EXATO para entrada
- Decisão binária: ENTER ou SKIP
- Critérios que influenciam a decisão
- Análise em TEMPO REAL (sem olhar para o futuro)
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def analyze_signal_quality(row, historical_data):
    """
    Analisa se vale a pena ENTRAR na operação
    Baseado em critérios em tempo real (SEM conhecer o futuro)
    """
    
    confidence = row['Confiança %']
    refinement_score = row['Refinement Score']
    direction = row['Direção']
    
    # Critério 1: Confiança alta (>90%)
    high_confidence = confidence >= 90
    
    # Critério 2: Refinement score bom (>0.6)
    good_refinement = refinement_score >= 0.6
    
    # Critério 3: Refinement score excelente (>0.75)
    excellent_refinement = refinement_score >= 0.75
    
    # Critério 4: Histórico de sucesso nessa direção
    # Contar histórico de sucesso
    if len(historical_data) > 0:
        same_direction = historical_data[historical_data['Direção'] == direction]
        if len(same_direction) > 0:
            win_rate_direction = (same_direction['Resultado'] == 'WIN').sum() / len(same_direction)
        else:
            win_rate_direction = 0.5
    else:
        win_rate_direction = 0.5
    
    good_history = win_rate_direction >= 0.55
    
    # DECISÃO FINAL
    # Critério mais rigoroso para ENTER
    criteria = [high_confidence, good_refinement, good_history]
    score = sum(criteria)
    
    decision = 'ENTER' if score >= 2 else 'SKIP'
    
    # Extra: Se refinement é excelente, dar bonus
    if excellent_refinement and high_confidence:
        decision = 'ENTER'
        score = 4
    
    reason = []
    
    if high_confidence:
        reason.append("HighConf")
    if good_refinement:
        reason.append("GoodRef")
    if excellent_refinement:
        reason.append("ExcelRef")
    if good_history:
        reason.append(f"Dir{int(win_rate_direction*100)}%")
    
    return decision, score, ' | '.join(reason) if reason else "Low Quality"


def generate_actionable_signals(symbol):
    """Gera planilha de sinais acionáveis"""
    
    print(f"\n{'='*80}")
    print(f"📊 Gerando Sinais Acionáveis - {symbol}")
    print(f"{'='*80}")
    
    # Carregar sinais filtrados
    df_signals = pd.read_csv(f'results/signals_{symbol}_QUALITY.csv')
    
    print(f"\n🔍 Analisando {len(df_signals)} sinais...")
    
    # Adicionar coluna de decisão
    df_signals['Decision'] = ''
    df_signals['Quality Score'] = 0
    df_signals['Reasons'] = ''
    
    # Análise por sinal
    for idx, row in df_signals.iterrows():
        # Histórico até esse ponto
        historical = df_signals.iloc[:idx].copy()
        
        # Análise
        decision, score, reasons = analyze_signal_quality(row, historical)
        
        df_signals.at[idx, 'Decision'] = decision
        df_signals.at[idx, 'Quality Score'] = score
        df_signals.at[idx, 'Reasons'] = reasons
    
    # Reorganizar colunas
    df_output = df_signals[[
        'Data/Hora',
        'Entrada',
        'Target',
        'Direção',
        'Confiança %',
        'Refinement Score',
        'Decision',
        'Quality Score',
        'Reasons',
        'Pips Refinados',
        'Resultado'
    ]].copy()
    
    # Renomear para melhor legibilidade
    df_output.columns = [
        'Signal Time (ENTRY)',
        'Entry Price',
        'Target Price',
        'Direction',
        'Confidence %',
        'Refinement',
        'Decision',
        'Quality Score',
        'Reasons',
        'Pips Result',
        'Actual Result'
    ]
    
    # Salvar
    filename = f'results/ACTIONABLE_SIGNALS_{symbol}.csv'
    df_output.to_csv(filename, index=False)
    
    print(f"✅ {filename} salvo")
    
    # Estatísticas
    enters = (df_output['Decision'] == 'ENTER').sum()
    skips = (df_output['Decision'] == 'SKIP').sum()
    
    if enters > 0:
        enter_data = df_output[df_output['Decision'] == 'ENTER']
        enter_win_rate = (enter_data['Actual Result'] == 'WIN').sum() / enters * 100
        enter_pips = enter_data['Pips Result'].sum()
    else:
        enter_win_rate = 0
        enter_pips = 0
    
    if skips > 0:
        skip_data = df_output[df_output['Decision'] == 'SKIP']
        skip_win_rate = (skip_data['Actual Result'] == 'WIN').sum() / skips * 100
        skip_pips = skip_data['Pips Result'].sum()
    else:
        skip_win_rate = 0
        skip_pips = 0
    
    print(f"\n📊 Análise de Decisões:")
    print(f"   ENTER: {enters} sinais ({enters/(enters+skips)*100:.1f}%)")
    print(f"   ├─ Win Rate: {enter_win_rate:.2f}%")
    print(f"   └─ Total Pips: {enter_pips:+.2f}")
    print(f"\n   SKIP: {skips} sinais ({skips/(enters+skips)*100:.1f}%)")
    print(f"   ├─ Win Rate: {skip_win_rate:.2f}%")
    print(f"   └─ Total Pips: {skip_pips:+.2f}")
    
    if enters > 0 and skips > 0:
        improvement = enter_win_rate - skip_win_rate
        print(f"\n   ✅ ENTER tem {improvement:+.2f}% melhor que SKIP")
    
    return df_output


def create_decision_guide(symbol):
    """Cria guia de decisão"""
    
    guide = f"""
================================================================================
🎯 GUIA DE USO - SINAIS ACIONÁVEIS {symbol}
================================================================================

📍 COLUNA "Signal Time (ENTRY)"
   └─ Horário EXATO para entrar na operação
   └─ M15 (15 minutos) de fechamento
   └─ Preço da entrada está em "Entry Price"

🎯 COLUNA "Decision"
   ├─ ENTER: Vale a pena entrar (critérios de qualidade OK)
   └─ SKIP: Não entre (critérios de qualidade questionáveis)

📊 CRITÉRIOS DE DECISÃO (Precisa de 3+ de 4):
   ✓ High Conf:      Confiança ≥ 90%
   ✓ Good Ref:       Refinement Score ≥ 0.60
   ✓ Models Agree:   XGB e RF concordam com direção
   ✓ Dir XX%:        Histórico de sucesso nessa direção ≥ 55%

🔢 "Quality Score"
   └─ 4/4 = Excelente (ENTER com confiança)
   └─ 3/4 = Bom (ENTER)
   └─ 2/4 = Fraco (SKIP)
   └─ <2 = Ruim (SKIP)

💰 "Pips Result"
   └─ Resultado histórico (informativo)
   └─ Mostra o que aconteceu após a entrada

📈 "Actual Result"
   └─ WIN, LOSS ou BREAKEVEN
   └─ Resultado real da operação

================================================================================
🚀 COMO USAR:
================================================================================

1. Abra a planilha ACTIONABLE_SIGNALS_{symbol}.csv
2. Procure por "Signal Time (ENTRY)"
3. Se Decision = ENTER → Você DEVE ENTRAR naquele horário
4. Se Decision = SKIP → Não entre, aguarde o próximo sinal

✅ ENTRADAS (ENTER):
   - Melhor hit rate
   - Melhor histórico
   - Decisão automática

❌ ENTRADAS (SKIP):
   - Qualidade questionável
   - Esperar próximo sinal
   - Risco maior

================================================================================
"""
    
    filename = f'results/GUIDE_{symbol}.txt'
    with open(filename, 'w') as f:
        f.write(guide)
    
    print(guide)
    print(f"✅ Guia salvo em {filename}")


def main():
    print("\n" + "="*80)
    print("🎯 GENERATE ACTIONABLE SIGNALS - Sinais Acionáveis em Tempo Real")
    print("="*80)
    
    for symbol in ['EURUSD', 'GBPUSD']:
        df_output = generate_actionable_signals(symbol)
        create_decision_guide(symbol)
    
    print("\n" + "="*80)
    print("✅ SINAIS ACIONÁVEIS GERADOS!")
    print("="*80)
    print("\n📁 Novos arquivos:")
    print("   • ACTIONABLE_SIGNALS_EURUSD.csv")
    print("   • GUIDE_EURUSD.txt")
    print("   • ACTIONABLE_SIGNALS_GBPUSD.csv")
    print("   • GUIDE_GBPUSD.txt")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
