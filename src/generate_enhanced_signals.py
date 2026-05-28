#!/usr/bin/env python3
"""
ENHANCED ACTIONABLE SIGNALS - Sinais Acionáveis Completos
==========================================================

Gera CSV com:
- Horário EXATO para entrada
- Preço de entrada
- Target PREDITO (o que os modelos predisseram)
- Preço REAL de fechamento (D+1 14:00)
- Decisão ENTER/SKIP
- Comparação predição vs real
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def generate_enhanced_signals(symbol):
    """Gera planilha de sinais acionáveis COMPLETA"""
    
    print(f"\n{'='*80}")
    print(f"📊 Gerando Sinais Acionáveis Completos - {symbol}")
    print(f"{'='*80}")
    
    # Carregar backtest detalhado
    df_detailed = pd.read_csv(f'results/backtest_{symbol}_DETAILED.csv')
    
    # Carregar sinais com decisão (ACTIONABLE_SIGNALS, não signals)
    df_signals = pd.read_csv(f'results/ACTIONABLE_SIGNALS_{symbol}.csv')
    
    print(f"\n🔍 Processando {len(df_signals)} sinais...")
    
    # Criar DataFrame de output
    output_data = []
    
    for idx, sig_row in df_signals.iterrows():
        entry_time = sig_row['Signal Time (ENTRY)']
        
        # Encontrar a linha no backtest detalhado
        detailed_row = df_detailed[df_detailed['timestamp'] == entry_time]
        
        if len(detailed_row) == 0:
            print(f"  ⚠️  Sinal {idx} não encontrado no backtest")
            continue
        
        detailed_row = detailed_row.iloc[0]
        
        # Dados de entrada
        entry_price = sig_row['Entry Price']
        target_price_predicted = sig_row['Target Price']
        actual_close = detailed_row['target_price']
        direction = sig_row['Direction']
        confidence = sig_row['Confidence %']
        refinement = sig_row['Refinement']
        decision = sig_row['Decision']  # ENTER ou SKIP
        quality_score = sig_row['Quality Score']
        reasons = sig_row['Reasons']
        
        # Calcular pips
        actual_pips_real = detailed_row['actual_pips']
        predicted_pips = sig_row['Pips Result']
        pips_error = actual_pips_real - predicted_pips
        
        result = sig_row['Actual Result']
        
        output_data.append({
            'Signal Time (ENTRY)': entry_time,
            'Entry Price': entry_price,
            'Direction': direction,
            'Target Predicted': target_price_predicted,
            'Actual Close D+1': actual_close,
            'Difference': actual_close - target_price_predicted,
            'Confidence %': confidence,
            'Refinement': refinement,
            'Quality Score': quality_score,
            'Decision': decision,
            'Predicted Pips': predicted_pips,
            'Actual Pips': actual_pips_real,
            'Pips Error': pips_error,
            'Reasons': reasons,
            'Result': result
        })
    
    df_output = pd.DataFrame(output_data)
    
    # Salvar CSV
    filename = f'results/ENHANCED_SIGNALS_{symbol}.csv'
    df_output.to_csv(filename, index=False)
    
    print(f"✅ {filename} salvo ({len(df_output)} sinais)")
    
    # Estatísticas
    print(f"\n📊 Estatísticas:")
    print(f"   Total Sinais: {len(df_output)}")
    
    enters = (df_output['Decision'] == 'ENTER').sum()
    skips = (df_output['Decision'] == 'SKIP').sum()
    
    print(f"\n   ENTER: {enters} sinais")
    if enters > 0:
        enter_data = df_output[df_output['Decision'] == 'ENTER']
        enter_win_rate = (enter_data['Result'] == 'WIN').sum() / enters * 100
        enter_pips = enter_data['Actual Pips'].sum()
        enter_pred_error = enter_data['Pips Error'].mean()
        
        print(f"   ├─ Win Rate: {enter_win_rate:.2f}%")
        print(f"   ├─ Total Pips: {enter_pips:+.2f}")
        print(f"   └─ Avg Prediction Error: {enter_pred_error:+.2f} pips")
    
    print(f"\n   SKIP: {skips} sinais")
    if skips > 0:
        skip_data = df_output[df_output['Decision'] == 'SKIP']
        skip_win_rate = (skip_data['Result'] == 'WIN').sum() / skips * 100
        skip_pips = skip_data['Actual Pips'].sum()
        skip_pred_error = skip_data['Pips Error'].mean()
        
        print(f"   ├─ Win Rate: {skip_win_rate:.2f}%")
        print(f"   ├─ Total Pips: {skip_pips:+.2f}")
        print(f"   └─ Avg Prediction Error: {skip_pred_error:+.2f} pips")
    
    # Accuracy da predição
    print(f"\n   📈 Acurácia de Predição:")
    mean_error = df_output['Pips Error'].mean()
    mae = df_output['Pips Error'].abs().mean()
    
    print(f"   ├─ Mean Error: {mean_error:+.2f} pips (viés)")
    print(f"   └─ MAE: {mae:.2f} pips (erro médio absoluto)")
    
    return df_output


def create_enhanced_guide():
    """Cria guia completo"""
    
    guide = """
================================================================================
📋 GUIA COMPLETO - SINAIS ACIONÁVEIS APRIMORADOS
================================================================================

🎯 ENTENDENDO AS COLUNAS
================================================================================

1️⃣ "Signal Time (ENTRY)"
   └─ Horário EXATO para entrar (M15 de fechamento)
   └─ Exemplo: 2025-09-04 00:15:00

2️⃣ "Entry Price"
   └─ Preço de entrada naquele horário
   └─ Exemplo: 1.16595

3️⃣ "Direction"
   └─ Direção da operação (UP ou DOWN)
   └─ UP = Compra (espera subir)
   └─ DOWN = Venda (espera cair)

4️⃣ "Target Predicted"
   └─ O preço que NOSSOS MODELOS PREDIZERAM
   └─ Baseado em XGBoost + RandomForest + Decision Tree
   └─ Exemplo: 1.16607 (predição)

5️⃣ "Actual Close D+1"
   └─ O preço REAL de fechamento no dia seguinte às 14:00
   └─ ISSO É O REAL, O QUE ACONTECEU
   └─ Exemplo: 1.17443 (realidade)

6️⃣ "Difference"
   └─ Target Predicted - Actual Close
   └─ Mostra o erro da predição
   └─ Positivo = Predição foi maior que real
   └─ Negativo = Predição foi menor que real

7️⃣ "Confidence %"
   └─ Confiança da predição (0-100%)
   └─ >90% = Muito confiável
   └─ Baseado na concordância entre XGB e RF

8️⃣ "Refinement"
   └─ Qualidade do refinamento da Decision Tree (0-1)
   └─ >0.75 = Excelente
   └─ 0.6-0.75 = Bom

9️⃣ "Quality Score"
   └─ 4/4 = Perfeito (ENTER com confiança máxima)
   └─ 3/4 = Bom (ENTER)
   └─ 2/4 = OK (ENTER)
   └─ <2 = Fraco (SKIP)

🔟 "Decision"
   └─ ENTER = Você DEVE ENTRAR nessa operação
   └─ SKIP = Não entre, espere o próximo sinal

1️⃣1️⃣ "Predicted Pips"
   └─ Pips que PREDIZEMOS (Target Predicted - Entry Price) * 10000
   └─ O que ESPERÁVAMOS ganhar/perder

1️⃣2️⃣ "Actual Pips"
   └─ Pips REAIS (Actual Close - Entry Price) * 10000
   └─ O QUE REALMENTE GANHOU/PERDEU

1️⃣3️⃣ "Pips Error"
   └─ Actual Pips - Predicted Pips
   └─ Diferença entre predição e realidade
   └─ Positivo = Predição foi pessimista (ganhou mais!)
   └─ Negativo = Predição foi otimista (ganhou menos)

1️⃣4️⃣ "Reasons"
   └─ Por que ENTER ou SKIP
   └─ HighConf = Confiança >90%
   └─ GoodRef = Refinement >0.6
   └─ ExcelRef = Refinement >0.75
   └─ DirXX% = Histórico de XX% de sucesso nessa direção

1️⃣5️⃣ "Result"
   └─ WIN = Ganhou pips
   └─ LOSS = Perdeu pips
   └─ BREAKEVEN = Sem ganho nem perda

================================================================================
🔍 EXEMPLO PRÁTICO
================================================================================

Linha 1:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Signal Time:           2025-09-04 00:15:00                                  │
│ Entry Price:           1.16595 (preço de entrada)                           │
│ Direction:             DOWN (venda)                                          │
│                                                                              │
│ PREDIÇÃO DOS MODELOS:                                                        │
│ ├─ Target Predicted:   1.16607 (o que os modelos acharam)                   │
│ ├─ Predicted Pips:     +12 pips (esperávamos ganhar 12 pips)               │
│                                                                              │
│ REALIDADE:                                                                   │
│ ├─ Actual Close D+1:   1.17443 (preço real no dia seguinte 14:00)          │
│ ├─ Actual Pips:        +84.8 pips (na verdade ganhou 84.8 pips!)           │
│ ├─ Pips Error:         +72.8 pips (a predição foi PESSIMISTA!)             │
│                                                                              │
│ ANÁLISE:                                                                     │
│ ├─ Confidence:         99.33% (muito confiável)                             │
│ ├─ Refinement:         0.607 (bom)                                          │
│ ├─ Decision:           ENTER (entre nessa!)                                 │
│ └─ Result:             LOSS (final foi LOSS em backtesting)                │
└─────────────────────────────────────────────────────────────────────────────┘

⚠️  NOTA: O "Pips Error" mostra que a predição subestimou o movimento!
    Os modelos são CONSERVADORES (predizem menos do que acontece realmente)

================================================================================
📊 INTERPRETAÇÃO
================================================================================

✅ BOAS OPERAÇÕES:
   • Confidence >95%
   • Refinement >0.7
   • Reasons com 3+ critérios
   • Quality Score = 4/4

❌ OPERAÇÕES FRACAS:
   • Confidence <90%
   • Refinement <0.6
   • Reasons com 1-2 critérios
   • Quality Score <2

📈 ERRO DE PREDIÇÃO:
   • Pips Error POSITIVO = Predição subestimou (BOAS! Ganhou mais)
   • Pips Error NEGATIVO = Predição superestimou (RUINS! Ganhou menos)

================================================================================
🎯 COMO USAR PARA TRADING
================================================================================

1. Abra ENHANCED_SIGNALS_{symbol}.csv
2. Procure linhas com:
   ├─ Decision = ENTER
   ├─ Quality Score ≥ 3
   ├─ Confidence > 95%
   └─ Refinement > 0.7

3. No horário "Signal Time (ENTRY)":
   ├─ Entre no preço "Entry Price"
   ├─ Na direção "Direction" (UP/DOWN)
   └─ Com alvo em "Target Predicted"

4. Rode até D+1 14:00 (próximo dia 14:00 exato)

5. Compare:
   ├─ Seu resultado com "Actual Pips"
   └─ Seu resultado com "Predicted Pips"

================================================================================
"""
    
    for symbol in ['EURUSD', 'GBPUSD']:
        filename = f'results/GUIDE_ENHANCED_{symbol}.txt'
        with open(filename, 'w') as f:
            f.write(guide)
        print(f"✅ Guia salvo em {filename}")


def main():
    print("\n" + "="*80)
    print("📊 ENHANCED ACTIONABLE SIGNALS - Sinais Completos com Predição vs Real")
    print("="*80)
    
    for symbol in ['EURUSD', 'GBPUSD']:
        generate_enhanced_signals(symbol)
    
    create_enhanced_guide()
    
    print("\n" + "="*80)
    print("✅ SINAIS ACIONÁVEIS APRIMORADOS GERADOS!")
    print("="*80)
    print("\n📁 Novos arquivos:")
    print("   • ENHANCED_SIGNALS_EURUSD.csv")
    print("   • ENHANCED_SIGNALS_GBPUSD.csv")
    print("   • GUIDE_ENHANCED_EURUSD.txt")
    print("   • GUIDE_ENHANCED_GBPUSD.txt")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
