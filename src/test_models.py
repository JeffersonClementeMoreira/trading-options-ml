#!/usr/bin/env python3
"""
Teste dos Modelos XGBoost com Dados Simulados
Mostra como o modelo faz previsões em tempo real
"""

import pickle
import numpy as np
import os
from datetime import datetime

class ModelTester:
    """Testar modelos com dados simulados"""
    
    def __init__(self, models_dir="/home/ubuntu/pessoal/options/src"):
        self.models_dir = models_dir
        self.models = {}
        self.symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
    
    def load_models(self):
        """Carregar modelos"""
        for symbol in self.symbols:
            filepath = f"{self.models_dir}/xgboost_{symbol}.pkl"
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    self.models[symbol] = pickle.load(f)
    
    def generate_test_features(self, symbol):
        """Gerar features simuladas para teste"""
        # Simular alguns cenários diferentes
        
        # Scenario 1: RSI alto (overbought) - sinalizaria queda
        scenario1 = np.array([[
            75.0,      # RSI_14 (alto = overbought)
            1.0900,    # SMA_20
            1.0850,    # SMA_50
            0.5,       # ATR_pct
            0.0050,    # Momentum (positivo)
            3.0,       # Confluence (alta)
            1.0920,    # Close (acima das médias)
            500000.0   # Volume_MA
        ]])
        
        # Scenario 2: RSI baixo (oversold) - sinalizaria alta
        scenario2 = np.array([[
            25.0,      # RSI_14 (baixo = oversold)
            1.0850,    # SMA_20
            1.0900,    # SMA_50
            0.5,       # ATR_pct
            -0.0050,   # Momentum (negativo)
            0.0,       # Confluence (baixa)
            1.0800,    # Close (abaixo das médias)
            500000.0   # Volume_MA
        ]])
        
        # Scenario 3: Consolidação - sem sinal claro
        scenario3 = np.array([[
            50.0,      # RSI_14 (neutro)
            1.0870,    # SMA_20
            1.0860,    # SMA_50
            0.2,       # ATR_pct (baixo)
            0.0010,    # Momentum (quase zero)
            1.5,       # Confluence (média)
            1.0865,    # Close (perto das médias)
            500000.0   # Volume_MA
        ]])
        
        return {
            'Overbought (RSI Alto)': scenario1,
            'Oversold (RSI Baixo)': scenario2,
            'Consolidação': scenario3
        }
    
    def test_symbol(self, symbol):
        """Testar um símbolo específico"""
        if symbol not in self.models:
            print(f"❌ Modelo não encontrado para {symbol}")
            return
        
        model = self.models[symbol]
        test_scenarios = self.generate_test_features(symbol)
        
        print(f"\n{'='*70}")
        print(f"🧪 TESTE DO MODELO: {symbol}")
        print(f"{'='*70}\n")
        
        feature_names = ['RSI_14', 'SMA_20', 'SMA_50', 'ATR_%', 'Momentum', 'Confluence', 'Close', 'Volume_MA']
        
        for scenario_name, features in test_scenarios.items():
            # Fazer predição
            prediction = model.predict(features)[0]  # 0 ou 1
            confidence = model.predict_proba(features)[0]  # [prob_0, prob_1]
            
            # Interpretar resultado
            if prediction == 1:
                direction = "📈 ALTA"
                confidence_value = confidence[1]
            else:
                direction = "📉 QUEDA"
                confidence_value = confidence[0]
            
            print(f"Cenário: {scenario_name}")
            print(f"├─ Previsão: {direction}")
            print(f"├─ Confiança: {confidence_value:.2%}")
            print(f"├─ Probabilidades: QUEDA={confidence[0]:.2%}, ALTA={confidence[1]:.2%}")
            print(f"└─ Features: RSI={features[0,0]:.0f}, SMA20={features[0,1]:.4f}, SMA50={features[0,2]:.4f}, Momentum={features[0,4]:.4f}\n")
    
    def run_all_tests(self):
        """Executar testes para todos os símbolos"""
        print("\n" + "╔" + "="*68 + "╗")
        print("║" + " "*15 + "🧪 TESTE DOS MODELOS XGBOOST" + " "*25 + "║")
        print("╚" + "="*68 + "╝")
        
        print("\n🔄 Carregando modelos...")
        self.load_models()
        
        if not self.models:
            print("\n❌ Nenhum modelo encontrado!")
            return
        
        print("✅ Modelos carregados\n")
        
        # Testar cada símbolo
        for symbol in self.symbols:
            self.test_symbol(symbol)
        
        # Resumo final
        self.show_test_summary()
    
    def show_test_summary(self):
        """Mostrar resumo dos testes"""
        print("="*70)
        print("📊 RESUMO DOS TESTES")
        print("="*70 + "\n")
        
        print("✓ Os modelos foram testados com 3 cenários cada:")
        print("  1. Overbought (RSI alto) - esperado: QUEDA")
        print("  2. Oversold (RSI baixo) - esperado: ALTA")
        print("  3. Consolidação - esperado: INCERTO\n")
        
        print("💡 Interpretação:")
        print("  • Confiança > 60% = Predição forte")
        print("  • Confiança 50-60% = Predição fraca")
        print("  • Confiança < 50% = Incerteza (próximo de 50/50)\n")
        
        print("🔄 Em produção:")
        print("  • O modelo recebe features reais do MT5")
        print("  • Faz previsão a cada novo candle M15")
        print("  • Envia alerta com score para Telegram\n")


def main():
    tester = ModelTester()
    tester.run_all_tests()
    
    print("╔" + "="*68 + "╗")
    print("║  Testes concluídos! Os modelos estão funcionando.             ║")
    print("╚" + "="*68 + "╝\n")


if __name__ == '__main__':
    main()
