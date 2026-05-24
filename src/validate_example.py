#!/usr/bin/env python3
"""
Validador automático do exemplo_backtest_integration.py
Verifica se tudo está correto
"""

import csv
import os

def validate_example():
    """Valida os arquivos gerados pelo exemplo"""
    
    print("\n" + "="*70)
    print("🔍 AUTO-VALIDATOR: example_backtest_integration.py")
    print("="*70 + "\n")
    
    # Check 1: Files exist
    print("✓ Check 1: Arquivos existem?")
    csv_file = "predictions/example_backtest.csv"
    html_file = "predictions/example_backtest.html"
    
    if not os.path.exists(csv_file):
        print(f"  ❌ ERRO: {csv_file} não encontrado")
        return False
    print(f"  ✅ {csv_file}")
    
    if not os.path.exists(html_file):
        print(f"  ❌ ERRO: {html_file} não encontrado")
        return False
    print(f"  ✅ {html_file}\n")
    
    # Check 2: Read CSV and validate
    print("✓ Check 2: Dados do CSV são válidos?")
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print("  ❌ ERRO: CSV vazio")
        return False
    print(f"  ✅ {len(rows)} linhas de dados\n")
    
    # Check 3: Validate each row
    print("✓ Check 3: Cada linha tem lógica correta?\n")
    
    all_valid = True
    
    for i, row in enumerate(rows, 1):
        # Parse probabilities
        try:
            p_up = float(row['p_up'])
            p_down = float(row['p_down'])
            p_flat = float(row['p_flat'])
            action = row['action']
            confidence = float(row['confidence'])
        except ValueError as e:
            print(f"  ❌ Linha {i}: Erro ao parsear - {e}")
            all_valid = False
            continue
        
        # Check probabilities sum to 1.0
        total = p_up + p_down + p_flat
        tolerance = 0.01  # Allow small rounding errors
        if abs(total - 1.0) > tolerance:
            print(f"  ❌ Linha {i}: Probabilidades não somam 100% (somam {total:.1%})")
            all_valid = False
            continue
        
        # Check action vs probabilities
        spread = abs(p_up - p_down)
        is_valid = False
        reason = ""
        
        if action == "CALL":
            is_valid = (p_up > p_down) and (confidence >= 0.55)
            reason = f"CALL: P(UP)={p_up:.1%} > P(DOWN)={p_down:.1%}, conf={confidence:.1%}"
        elif action == "PUT":
            is_valid = (p_down > p_up) and (confidence >= 0.55)
            reason = f"PUT: P(DOWN)={p_down:.1%} > P(UP)={p_up:.1%}, conf={confidence:.1%}"
        elif action == "STRANGLE":
            is_valid = (spread < 0.40) and (confidence >= 0.55)
            reason = f"STRANGLE: spread={spread:.1%} < 40%, conf={confidence:.1%}"
        elif action == "NO_TRADE":
            is_valid = confidence < 0.55
            reason = f"NO_TRADE: conf={confidence:.1%} < 55%"
        else:
            is_valid = False
            reason = f"Action '{action}' não é válida"
        
        status = "✅" if is_valid else "❌"
        print(f"  {status} Linha {i}: {reason}")
        
        if not is_valid:
            all_valid = False
    
    print()
    
    # Check 4: HTML content
    print("✓ Check 4: HTML tem as cores corretas?")
    
    with open(html_file, 'r') as f:
        html_content = f.read()
    
    colors = {
        "#90EE90": "CALL (verde)",
        "#FFB6C6": "PUT (vermelho)",
        "#FFD700": "STRANGLE (ouro)",
        "#D3D3D3": "NO_TRADE (cinza)",
    }
    
    for color, name in colors.items():
        if color in html_content:
            print(f"  ✅ {color} ({name})")
        # else: color can be missing if action not used
    
    print()
    
    # Final report
    print("="*70)
    if all_valid:
        print("✅ VALIDAÇÃO PASSOU - Tudo está correto!")
        print("="*70)
        print("\nSeu exemplo está funcionando perfeitamente!")
        print("Próximo passo: integrar no xgb_entry_optimizer.py")
        return True
    else:
        print("❌ VALIDAÇÃO FALHOU - Há erros nos dados")
        print("="*70)
        return False


if __name__ == "__main__":
    success = validate_example()
    exit(0 if success else 1)
