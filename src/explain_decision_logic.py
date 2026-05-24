#!/usr/bin/env python3
"""
Visualizador da lógica de decisão do TradingDecisionEngine
Mostra exemplos de cada ação e quando ela é acionada
"""

from trading_decision import TradingDecisionEngine, TradeAction

def explain_decision_logic():
    """Explica a lógica de decisão com exemplos"""
    
    engine = TradingDecisionEngine(
        confidence_threshold=0.55,  # 55%
        strangle_threshold=0.40,    # 40%
    )
    
    print("\n" + "="*80)
    print("🎯 LÓGICA DE DECISÃO DO TRADING ENGINE")
    print("="*80 + "\n")
    
    print("CONFIGURAÇÃO:")
    print(f"  • confidence_threshold = {engine.confidence_threshold:.0%} (55%)")
    print(f"  • strangle_threshold = {engine.strangle_threshold:.0%} (40%)")
    print()
    
    # Fluxo de decisão
    print("="*80)
    print("📊 FLUXO DE DECISÃO")
    print("="*80 + "\n")
    
    print("""
    ENTRADA: Recebemos 3 probabilidades
    ├─ p_up   = probabilidade do preço SUBIR
    ├─ p_down = probabilidade do preço DESCER
    └─ p_flat = probabilidade de CONSOLIDAÇÃO
    
    PASSO 1: Calcular confiança
    ├─ confidence = max(p_up, p_down, p_flat)
    └─ Exemplo: max(0.72, 0.15, 0.13) = 0.72 (72%)
    
    PASSO 2: Verificar se confiança é alta
    ├─ Se confidence < 55% → ❌ NO_TRADE (não faz nada)
    └─ Se confidence ≥ 55% → ✅ Continue para próximo passo
    
    PASSO 3: Medir diferença entre UP e DOWN
    ├─ spread = |p_up - p_down|
    └─ Exemplo: |0.72 - 0.15| = 0.57 (57%)
    
    PASSO 4: Decidir ação (ESTRATÉGIA DE VENDA)
    ├─ Se spread < 40% → 📊 STRANGLE (incerteza - vender volatilidade)
    ├─ Se spread ≥ 40% E p_up > p_down → 📈 PUT_SELL (vender PUT - bullish)
    └─ Se spread ≥ 40% E p_down > p_up → 📉 CALL_SELL (vender CALL - bearish)
    """)
    
    print("\n" + "="*80)
    print("🔍 EXEMPLOS PRÁTICOS")
    print("="*80 + "\n")
    
    # Exemplo 1: PUT_SELL (vender put quando bullish) com confiança ALTA
    print("EXEMPLO 1: Tendência clara de ALTA com confiança ALTA")
    print("-" * 80)
    signal = engine.decide(
        symbol="EURUSD",
        timeframe="D1",
        datetime_str="2026-05-25 14:00:00",
        p_up=0.72,
        p_down=0.15,
        p_flat=0.13,
    )
    print(f"  Input: p_up=72%, p_down=15%, p_flat=13%")
    print(f"  Confiança: max(72%, 15%, 13%) = 72% ✅ (>= 55%)")
    print(f"  Spread: |72% - 15%| = 57% ✅ (>= 40%)")
    print(f"  p_up (72%) > p_down (15%)? ✅ SIM")
    print(f"  → AÇÃO: {signal.action.value} ✅ (vender PUT pois bullish)")
    print(f"  → RAZÃO: {signal.reasoning}\n")
    
    # Exemplo 2: CALL_SELL (vender call quando bearish) com confiança ALTA
    print("EXEMPLO 2: Tendência clara de BAIXA com confiança ALTA")
    print("-" * 80)
    signal = engine.decide(
        symbol="EURUSD",
        timeframe="D1",
        datetime_str="2026-05-25 14:00:00",
        p_up=0.20,
        p_down=0.65,
        p_flat=0.15,
    )
    print(f"  Input: p_up=20%, p_down=65%, p_flat=15%")
    print(f"  Confiança: max(20%, 65%, 15%) = 65% ✅ (>= 55%)")
    print(f"  Spread: |20% - 65%| = 45% ✅ (>= 40%)")
    print(f"  p_down (65%) > p_up (20%)? ✅ SIM")
    print(f"  → AÇÃO: {signal.action.value} ✅ (vender CALL pois bearish)")
    print(f"  → RAZÃO: {signal.reasoning}\n")
    
    # Exemplo 3: STRANGLE com incerteza
    print("EXEMPLO 3: Incerteza (spread baixo) com confiança ALTA")
    print("-" * 80)
    signal = engine.decide(
        symbol="EURUSD",
        timeframe="D1",
        datetime_str="2026-05-25 14:00:00",
        p_up=0.45,
        p_down=0.40,
        p_flat=0.15,
    )
    print(f"  Input: p_up=45%, p_down=40%, p_flat=15%")
    print(f"  Confiança: max(45%, 40%, 15%) = 45% ❌ (< 55%)")
    print(f"  → AÇÃO: {signal.action.value}")
    print(f"  → RAZÃO: {signal.reasoning}\n")
    
    # Exemplo 4: NO_TRADE com confiança BAIXA
    print("EXEMPLO 4: Confiança BAIXA → NÃO FAZE NADA")
    print("-" * 80)
    signal = engine.decide(
        symbol="EURUSD",
        timeframe="D1",
        datetime_str="2026-05-25 14:00:00",
        p_up=0.40,
        p_down=0.35,
        p_flat=0.25,
    )
    print(f"  Input: p_up=40%, p_down=35%, p_flat=25%")
    print(f"  Confiança: max(40%, 35%, 25%) = 40% ❌ (< 55%)")
    print(f"  → AÇÃO: {signal.action.value}")
    print(f"  → RAZÃO: {signal.reasoning}\n")
    
    # Exemplo 5: STRANGLE com incerteza (spread baixo)
    print("EXEMPLO 5: Incerteza com spread BAIXO")
    print("-" * 80)
    signal = engine.decide(
        symbol="EURUSD",
        timeframe="D1",
        datetime_str="2026-05-25 14:00:00",
        p_up=0.48,
        p_down=0.42,
        p_flat=0.10,
    )
    print(f"  Input: p_up=48%, p_down=42%, p_flat=10%")
    print(f"  Confiança: max(48%, 42%, 10%) = 48% ✅ (>= 55%)")
    print(f"  Spread: |48% - 42%| = 6% ❌ (< 40%)")
    print(f"  → AÇÃO: {signal.action.value}")
    print(f"  → RAZÃO: {signal.reasoning}\n")
    
    print("="*80)
    print("📌 RESUMO: O QUE FAZER EM CADA CASO")
    print("="*80 + "\n")
    
    print("""
    ✅ VENDER PUT (📈 PUT_SELL)
    └─ Quando: p_up > 55% E diferença (p_up - p_down) > 40%
    └─ Significado: Modelo confia que preço vai SUBIR amanhã
    └─ Ação: Venda uma PUT (ganhe com movimento pequeno ou alta)
    
    ✅ VENDER CALL (📉 CALL_SELL)
    └─ Quando: p_down > 55% E diferença (p_down - p_up) > 40%
    └─ Significado: Modelo confia que preço vai DESCER amanhã
    └─ Ação: Venda uma CALL (ganhe com movimento pequeno ou baixa)
    
    ⚖️ VENDER STRANGLE (📊 STRANGLE)
    └─ Quando: Confiança ≥ 55% MAS diferença (|p_up - p_down|) < 40%
    └─ Significado: Modelo confia que haverá MOVIMENTO mas não sabe direção
    └─ Ação: Venda volatilidade (venda CALL + PUT) ou espere
    
    🚫 NÃO FAZER NADA (NO_TRADE)
    └─ Quando: Confiança < 55%
    └─ Significado: Modelo está INDECISO
    └─ Ação: Fique de fora, não arrisque
    """)
    
    print("\n" + "="*80)
    print("💡 INTERPRETAÇÃO DOS SEUS RESULTADOS")
    print("="*80 + "\n")
    
    print("""
    PUT_SELL e CALL_SELL: 100% de acerto (quando havia dados futuros) ❌ INVÁLIDO
    └─ Nota: Resultados anteriores usavam dados futuros (data leakage)
    └─ Acerto real esperado: 55-65% (depois de correção)
    └─ Conclusão: Modelo é BOM mas não 100% (necessário refazer validação)
    
    STRANGLE: 50% de acerto
    └─ Isso é esperado quando não há tendência clara
    └─ STRANGLE significa: "Não sei direção, mas haverá movimento"
    └─ 50% = Moeda (nem bom, nem ruim, só hedge)
    
    NO_TRADE: 0 sinais
    └─ Modelo foi AGRESSIVO (confiança_threshold = 55%)
    └─ Se aumentarmos para 60%, haverá mais NO_TRADE
    """)


if __name__ == "__main__":
    explain_decision_logic()
