#!/bin/bash

# 📂 COMO USAR CADA PASTA DO PROJETO

cd /home/ubuntu/pessoal/options

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════╗
║           🎯 INSTRUÇÕES - COMO USAR O PROJETO ORGANIZADO                 ║
╚════════════════════════════════════════════════════════════════════════════╝

📁 CADA PASTA FAZ ALGO ESPECÍFICO:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 results/ - RESULTADOS DO BACKTEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Contém os arquivos CSV com predições e resultados reais

  Arquivos:
    ├── backtest_EURUSD_regressor_correct.csv  (681 KB, 6.731 linhas)
    └── backtest_GBPUSD_regressor_correct.csv  (682 KB, 6.731 linhas)

  Como usar:
    # Ver primeiras linhas
    head -20 results/backtest_EURUSD_regressor_correct.csv

    # Contar registros
    wc -l results/backtest_EURUSD_regressor_correct.csv

    # Analisar em Python
    python3 -c "
    import pandas as pd
    df = pd.read_csv('results/backtest_EURUSD_regressor_correct.csv')
    print(f'Total Pips: {df[\"actual_pips\"].sum():.2f}')
    print(f'Win Rate: {(df[\"actual_pips\"] > 0).sum() / len(df) * 100:.2f}%')
    "

    # Copiar para análise em Excel
    cp results/backtest_*.csv ~/Desktop/


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 data/ - DADOS DE ENTRADA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Contém os dados históricos e dados processados com indicadores

  Arquivos:
    ├── EURUSD_M15_202401012200_202605222015.csv    (dados brutos)
    ├── GBPUSD_M15_202401012200_202605222015.csv    (dados brutos)
    ├── bt_analysis_EURUSD.csv                       (com indicadores)
    └── bt_analysis_GBPUSD.csv                       (com indicadores)

  Como usar:
    # Ver estrutura dos dados brutos
    head -5 data/EURUSD_M15_202401012200_202605222015.csv

    # Ver dados com indicadores
    head -5 data/bt_analysis_EURUSD.csv

    # Contar candles
    wc -l data/EURUSD_M15_202401012200_202605222015.csv


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 models/ - MODELOS TREINADOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Contém modelos salvos em pickle (.pkl)

  Modelos principais:
    ├── ml_ensemble_eurusd.pkl           (Ensemble XGBoost + RF - EURUSD)
    ├── ml_ensemble_gbpusd.pkl           (Ensemble XGBoost + RF - GBPUSD)
    ├── ml_scaler_eurusd.pkl             (StandardScaler - EURUSD)
    └── ml_scaler_gbpusd.pkl             (StandardScaler - GBPUSD)

  Como usar em Python:
    import pickle
    
    # Carregar modelo
    with open('models/ml_ensemble_eurusd.pkl', 'rb') as f:
        model = pickle.load(f)
    
    # Carregar scaler
    with open('models/ml_scaler_eurusd.pkl', 'rb') as f:
        scaler = pickle.load(f)
    
    # Normalizar dados e prever
    X_scaled = scaler.transform(X)
    predictions = model.predict(X_scaled)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🐍 src/ - SCRIPTS PYTHON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Contém scripts para treinamento, backtest e análise

  SCRIPTS PRINCIPAIS (usar estes):
    ├── backtest_regressor_correct.py       ← RODAR BACKTEST
    │   └─ Usa: data/bt_analysis_*.csv
    │   └─ Salva: results/backtest_*.csv
    │
    └── analyze_backtest_regressor.py       ← ANALISAR RESULTADOS
        └─ Lê: results/backtest_*.csv
        └─ Mostra: estatísticas, melhores/piores trades

  Outros scripts:
    ├── train_ensemble_final.py              (treinar modelos)
    ├── train_xgboost_model.py               (treinar XGBoost)
    └── ... (40+ scripts)

  Como usar:
    # Rodar backtest
    python3 src/backtest_regressor_correct.py

    # Analisar resultados
    python3 src/analyze_backtest_regressor.py


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 docs/ - DOCUMENTAÇÃO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Contém documentação importante do projeto

  Arquivos:
    └── REGRAS_CRITICAS.md   ← 🔴 LER ISSO!

  REGRAS CRÍTICAS (nunca esquecer):
    1. TARGET = PREÇO (não UP/DOWN)
    2. SEMPRE 14:00 UTC próximo dia
    3. NUNCA dados inventados
    4. NUNCA treinar 100% (sempre 70/30)
    5. REGRESSÃO (não classificação)

  Como ler:
    cat docs/REGRAS_CRITICAS.md


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 FLUXO DE TRABALHO RECOMENDADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Ir para pasta do projeto
   cd /home/ubuntu/pessoal/options

2. Rodar backtest (cria results/*.csv)
   python3 src/backtest_regressor_correct.py

3. Analisar resultados
   python3 src/analyze_backtest_regressor.py

4. Visualizar CSV
   head -20 results/backtest_EURUSD_regressor_correct.csv

5. Exportar para análise em Excel
   cp results/backtest_*.csv ~/Desktop/


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 CHECKLIST DE ARQUIVOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Backtest Results:
  ✅ results/backtest_EURUSD_regressor_correct.csv
  ✅ results/backtest_GBPUSD_regressor_correct.csv

Dados de Entrada:
  ✅ data/EURUSD_M15_202401012200_202605222015.csv
  ✅ data/GBPUSD_M15_202401012200_202605222015.csv
  ✅ data/bt_analysis_EURUSD.csv
  ✅ data/bt_analysis_GBPUSD.csv

Modelos Principais:
  ✅ models/ml_ensemble_eurusd.pkl
  ✅ models/ml_ensemble_gbpusd.pkl
  ✅ models/ml_scaler_eurusd.pkl
  ✅ models/ml_scaler_gbpusd.pkl

Scripts Principais:
  ✅ src/backtest_regressor_correct.py
  ✅ src/analyze_backtest_regressor.py

Documentação:
  ✅ docs/REGRAS_CRITICAS.md
  ✅ STRUCTURE.md (você está lendo!)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 DICAS RÁPIDAS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Listar todos os arquivos
ls -lhR /home/ubuntu/pessoal/options/

# Tamanho total
du -sh /home/ubuntu/pessoal/options/*

# Procurar arquivo
find /home/ubuntu/pessoal/options/ -name "*.csv"

# Contar linhas de código
find src/ -name "*.py" -exec wc -l {} +

# Buscar em arquivos
grep -r "função_procurada" src/


═════════════════════════════════════════════════════════════════════════════

✅ TUDO PRONTO PARA USO!

Local: /home/ubuntu/pessoal/options/

Próximo passo:
  python3 src/backtest_regressor_correct.py

═════════════════════════════════════════════════════════════════════════════

EOF
