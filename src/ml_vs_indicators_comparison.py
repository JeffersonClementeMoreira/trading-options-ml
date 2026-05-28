#!/usr/bin/env python3
"""
Comparação: ML Models vs Indicadores Puros
- Treina múltiplos modelos ML
- Compara performance vs baseline (indicadores)
- Mostra se há melhoria
"""

import csv
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
import warnings
warnings.filterwarnings('ignore')

class MLComparison:
    def __init__(self, csv_file, symbol):
        self.csv_file = csv_file
        self.symbol = symbol
        self.data = []
        self.X = []
        self.y = []
        
    def load_data(self):
        """Carrega dados com indicadores"""
        print(f"Carregando dados de {self.symbol}...")
        try:
            with open(self.csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.data.append({
                        'rsi': float(row['rsi']),
                        'sma20': float(row['sma20']),
                        'sma50': float(row['sma50']),
                        'macd': float(row['macd']),
                        'atr': float(row['atr']),
                        'momentum': float(row['momentum']),
                        'price_above_sma20': int(row['price_above_sma20']),
                        'price_above_sma50': int(row['price_above_sma50']),
                        'rsi_oversold': int(row['rsi_oversold']),
                        'rsi_overbought': int(row['rsi_overbought']),
                        'macd_positive': int(row['macd_positive']),
                        'momentum_positive': int(row['momentum_positive']),
                        'close': float(row['close']),
                        'volume': int(row['volume']),
                        'target_direction': 1 if row['target_direction'] == 'UP' else 0
                    })
            
            print(f"✅ Carregados {len(self.data)} registros")
            return len(self.data) > 0
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
    
    def prepare_features(self):
        """Prepara features para ML"""
        feature_names = ['rsi', 'sma20', 'sma50', 'macd', 'atr', 'momentum',
                        'price_above_sma20', 'price_above_sma50',
                        'rsi_oversold', 'rsi_overbought', 'macd_positive', 'momentum_positive']
        
        for row in self.data:
            features = [row[name] for name in feature_names]
            self.X.append(features)
            self.y.append(row['target_direction'])
        
        self.X = np.array(self.X)
        self.y = np.array(self.y)
        print(f"✅ {len(self.X)} amostras preparadas com {len(feature_names)} features")
    
    def baseline_score(self):
        """Calcula score baseline (indicadores puros)"""
        print("\n🔵 BASELINE (Indicadores Puros)")
        print("-" * 50)
        
        correct = 0
        for row in self.data:
            # Mesma lógica dos indicadores
            if row['rsi'] < 30:
                predicted = 1  # UP
            elif row['rsi'] > 70:
                predicted = 0  # DOWN
            else:
                predicted = 1 if row['macd_positive'] else 0
            
            if predicted == row['target_direction']:
                correct += 1
        
        accuracy = (correct / len(self.data)) * 100
        print(f"Acurácia: {accuracy:.2f}% ({correct}/{len(self.data)})")
        return accuracy
    
    def train_models(self):
        """Treina múltiplos modelos ML"""
        print("\n🟣 MACHINE LEARNING MODELS")
        print("-" * 50)
        
        # Dividir em treino/teste
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42
        )
        
        print(f"Treino: {len(X_train)} | Teste: {len(X_test)}")
        
        results = {}
        
        # 1. Random Forest
        print("\n1️⃣  Random Forest...", end=" ", flush=True)
        rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_test)
        rf_acc = accuracy_score(y_test, rf_pred) * 100
        print(f"✅ {rf_acc:.2f}%")
        results['Random Forest'] = {'model': rf, 'accuracy': rf_acc, 'pred': rf_pred}
        
        # 2. Gradient Boosting
        print("2️⃣  Gradient Boosting...", end=" ", flush=True)
        gb = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
        gb.fit(X_train, y_train)
        gb_pred = gb.predict(X_test)
        gb_acc = accuracy_score(y_test, gb_pred) * 100
        print(f"✅ {gb_acc:.2f}%")
        results['Gradient Boosting'] = {'model': gb, 'accuracy': gb_acc, 'pred': gb_pred}
        
        # 3. Logistic Regression
        print("3️⃣  Logistic Regression...", end=" ", flush=True)
        lr = LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1)
        lr.fit(X_train, y_train)
        lr_pred = lr.predict(X_test)
        lr_acc = accuracy_score(y_test, lr_pred) * 100
        print(f"✅ {lr_acc:.2f}%")
        results['Logistic Regression'] = {'model': lr, 'accuracy': lr_acc, 'pred': lr_pred}
        
        return results, X_test, y_test
    
    def compare_results(self, baseline_acc, ml_results):
        """Compara baseline vs ML"""
        print("\n" + "="*70)
        print(f"COMPARAÇÃO - {self.symbol}")
        print("="*70)
        
        print(f"\nBASELINE (Indicadores):        {baseline_acc:.2f}%")
        
        best_ml_acc = 0
        best_ml_name = None
        
        for name, result in sorted(ml_results.items(), key=lambda x: x[1]['accuracy'], reverse=True):
            improvement = result['accuracy'] - baseline_acc
            symbol = "📈" if improvement > 0 else "📉"
            print(f"{name:<25} {result['accuracy']:>7.2f}%  {symbol} {improvement:+.2f}%")
            if result['accuracy'] > best_ml_acc:
                best_ml_acc = result['accuracy']
                best_ml_name = name
        
        print("\n" + "-"*70)
        if best_ml_acc > baseline_acc:
            improvement = best_ml_acc - baseline_acc
            print(f"✅ ML MELHORA: {improvement:.2f}% pontos percentuais!")
            print(f"   Melhor modelo: {best_ml_name}")
        else:
            difference = baseline_acc - best_ml_acc
            print(f"❌ Indicadores são melhores: {difference:.2f}% pontos percentuais")
            print(f"   Conclusão: MANTER indicadores puros (KISS)")
        print("-"*70)
        
        return best_ml_name, best_ml_acc

def main():
    print("="*70)
    print("ML MODEL vs INDICADORES PUROS - COMPARAÇÃO REAL")
    print("="*70)
    
    for symbol, csv_file in [
        ('EURUSD', '/tmp/bt_analysis_EURUSD.csv'),
        ('GBPUSD', '/tmp/bt_analysis_GBPUSD.csv')
    ]:
        print(f"\n{'='*70}")
        print(f"Analisando {symbol}...")
        print(f"{'='*70}")
        
        comp = MLComparison(csv_file, symbol)
        
        if not comp.load_data():
            continue
        
        comp.prepare_features()
        baseline_acc = comp.baseline_score()
        ml_results, X_test, y_test = comp.train_models()
        best_ml, best_ml_acc = comp.compare_results(baseline_acc, ml_results)
    
    print("\n" + "="*70)
    print("RESUMO EXECUTIVO")
    print("="*70)
    print("""
PERGUNTA: ML Model melhora o resultado?

RESPOSTA: Depende do ativo e do modelo, mas em geral:

✅ VANTAGENS DO ML:
   • Pode capturar padrões complexos entre indicadores
   • Melhor em mercados com comportamento não-linear
   • Ensemble methods (Random Forest, Gradient Boosting) são poderosos

❌ DESVANTAGENS DO ML:
   • Risco de overfitting em dados limitados
   • Mais lento para produção (predicção em tempo real)
   • Menos interpretável ("caixa preta")
   • Pode não generalizar bem para dados futuros

🎯 RECOMENDAÇÃO:
   1. Se ML_accuracy > Baseline_accuracy em 2%+:
      → Usar ML (melhoria significativa)
   
   2. Se ML_accuracy ≈ Baseline_accuracy (±1%):
      → Manter indicadores (KISS principle)
   
   3. Se ML_accuracy < Baseline_accuracy:
      → Indicadores puros são superiores

PRÓXIMOS PASSOS:
   [ ] Testar ML com dados dos últimos 30 dias (mais recentes)
   [ ] Usar Walk-Forward Analysis (dados históricos → teste)
   [ ] Ensemble: Combinar indicadores + ML
   [ ] Otimizar hiperparâmetros do melhor modelo
""")
    print("="*70)

if __name__ == "__main__":
    main()
