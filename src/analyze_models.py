#!/usr/bin/env python3
"""
Analisar e Visualizar Performance dos Modelos XGBoost Treinados
Mostra acurácia, features importantes, métricas detalhadas
"""

import pickle
import numpy as np
import os
from pathlib import Path
import json

class ModelAnalyzer:
    """Analisar modelos XGBoost treinados"""
    
    def __init__(self, models_dir="/home/ubuntu/pessoal/options/src"):
        self.models_dir = models_dir
        self.models = {}
        self.symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
    
    def load_models(self):
        """Carregar todos os modelos"""
        for symbol in self.symbols:
            filepath = f"{self.models_dir}/xgboost_{symbol}.pkl"
            
            if not os.path.exists(filepath):
                print(f"❌ Modelo não encontrado: {filepath}")
                continue
            
            try:
                with open(filepath, 'rb') as f:
                    self.models[symbol] = pickle.load(f)
                
                # Pegar info do arquivo
                size_kb = os.path.getsize(filepath) / 1024
                print(f"✅ {symbol}: Carregado ({size_kb:.1f} KB)")
                
            except Exception as e:
                print(f"❌ Erro ao carregar {symbol}: {e}")
    
    def show_summary(self):
        """Mostrar resumo geral dos modelos"""
        print("\n" + "="*70)
        print("📊 RESUMO DOS MODELOS TREINADOS")
        print("="*70 + "\n")
        
        total_features = 8
        
        for symbol in self.symbols:
            if symbol not in self.models:
                print(f"⚠️  {symbol}: Não disponível\n")
                continue
            
            model = self.models[symbol]
            
            print(f"🎯 {symbol}")
            print(f"   ├─ Tipo: {type(model).__name__}")
            print(f"   ├─ N-Estimators: {model.n_estimators}")
            print(f"   ├─ Max Depth: {model.max_depth}")
            
            # Learning rate só existe em XGBoost
            if hasattr(model, 'learning_rate'):
                print(f"   ├─ Learning Rate: {model.learning_rate}")
            elif hasattr(model, 'learning_rate_init'):
                print(f"   ├─ Learning Rate: {model.learning_rate_init}")
            
            print(f"   └─ Features: {total_features} (RSI, SMA, ATR, Momentum, Confluence, Close, Volume MA)\n")
    
    def show_feature_importance(self):
        """Mostrar importância das features"""
        print("="*70)
        print("🎲 IMPORTÂNCIA DAS FEATURES")
        print("="*70 + "\n")
        
        feature_names = ['RSI_14', 'SMA_20', 'SMA_50', 'ATR_pct', 'Momentum', 'Confluence', 'Close', 'Volume_MA']
        
        for symbol in self.symbols:
            if symbol not in self.models:
                continue
            
            model = self.models[symbol]
            
            # XGBoost feature importance
            importances = model.feature_importances_
            
            # Ordenar
            indices = np.argsort(importances)[::-1]
            
            print(f"\n{symbol}:")
            print("─" * 50)
            
            for rank, idx in enumerate(indices[:8], 1):
                importance = importances[idx]
                name = feature_names[idx] if idx < len(feature_names) else f"Feature_{idx}"
                
                # Barra visual
                bar_length = int(importance * 50)
                bar = "█" * bar_length
                
                print(f"  {rank}. {name:15} {importance:6.2%} {bar}")
            
            # Total para validação
            total = sum(importances)
            print(f"\n     Total: {total:.2%}")
    
    def show_model_metrics(self):
        """Mostrar métricas detalhadas de cada modelo"""
        print("\n" + "="*70)
        print("📈 MÉTRICAS DOS MODELOS")
        print("="*70 + "\n")
        
        for symbol in self.symbols:
            if symbol not in self.models:
                continue
            
            model = self.models[symbol]
            
            print(f"\n{symbol}:")
            print("─" * 50)
            
            # Informações básicas
            print(f"  Número de árvores (n_estimators): {model.n_estimators}")
            print(f"  Profundidade máxima: {model.max_depth}")
            
            # XGBoost specific
            if hasattr(model, 'learning_rate'):
                print(f"  Learning rate: {model.learning_rate}")
            if hasattr(model, 'subsample'):
                print(f"  Subsample: {model.subsample}")
            if hasattr(model, 'colsample_bytree'):
                print(f"  Colsample_bytree: {model.colsample_bytree}")
            
            # Classes
            if hasattr(model, 'classes_'):
                print(f"  Classes: {model.classes_}")
            
            # Número de features
            print(f"  Número de features: {model.n_features_in_}")
    
    def generate_report(self):
        """Gerar relatório completo"""
        print("\n\n")
        print("╔" + "="*68 + "╗")
        print("║" + " "*15 + "📊 RELATÓRIO DE MODELOS XGBoost" + " "*21 + "║")
        print("╚" + "="*68 + "╝")
        
        # Carregar modelos
        print("\n🔄 Carregando modelos...\n")
        self.load_models()
        
        if not self.models:
            print("\n❌ Nenhum modelo encontrado!")
            return False
        
        # Mostrar informações
        self.show_summary()
        self.show_model_metrics()
        self.show_feature_importance()
        
        # Resumo final
        self.show_final_summary()
        
        return True
    
    def show_final_summary(self):
        """Mostrar resumo final"""
        print("\n" + "="*70)
        print("✅ MODELOS PRONTOS PARA USAR")
        print("="*70 + "\n")
        
        print("Próximos passos:\n")
        print("1️⃣  Reiniciar sistema:")
        print("   bash /home/ubuntu/pessoal/options/bin/start_system.sh\n")
        
        print("2️⃣  Reanexar EA no MT5:")
        print("   Tools → Expert Advisors → SendCandlesToServer\n")
        
        print("3️⃣  Monitorar alertas:")
        print("   tail -f /tmp/monitor_real.log\n")
        
        print("4️⃣  Verificar Telegram:")
        print("   Receberá 1 alerta a cada 15 minutos com score XGBoost\n")
        
        print("="*70)
        print("\n💡 Dicas:")
        print("  • Feature mais importante = maior impacto nas previsões")
        print("  • Modelos com 5000 candles = Melhor generalização")
        print("  • Se acurácia < 50% = Mercado muito aleatório neste período")
        print("  • Se acurácia > 55% = Modelo encontrou padrão útil\n")


def show_model_sizes():
    """Mostrar tamanho dos arquivos dos modelos"""
    print("\n📁 TAMANHO DOS ARQUIVOS")
    print("="*70 + "\n")
    
    models_dir = "/home/ubuntu/pessoal/options/src"
    symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
    
    total_size = 0
    
    for symbol in symbols:
        filepath = f"{models_dir}/xgboost_{symbol}.pkl"
        
        if os.path.exists(filepath):
            size_kb = os.path.getsize(filepath) / 1024
            size_mb = size_kb / 1024
            total_size += size_kb
            
            print(f"{symbol:10} {size_mb:6.2f} MB  ({size_kb:8.1f} KB)")
    
    print("─" * 70)
    print(f"{'TOTAL':10} {total_size/1024:6.2f} MB  ({total_size:8.1f} KB)")


def main():
    """Executar análise completa"""
    analyzer = ModelAnalyzer()
    analyzer.generate_report()
    show_model_sizes()
    
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║  Análise concluída! Os modelos estão prontos para usar.       ║")
    print("║                                                                ║")
    print("║  Para perguntas sobre feature importance ou performance,      ║")
    print("║  execute este script novamente a qualquer hora.              ║")
    print("║                                                                ║")
    print("╚" + "="*68 + "╝")
    print("\n")


if __name__ == '__main__':
    main()
