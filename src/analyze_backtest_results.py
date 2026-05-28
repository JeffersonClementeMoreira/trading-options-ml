#!/usr/bin/env python3
"""
Análise detalhada dos resultados de backtesting

Carrega arquivo CSV gerado e realiza análise:
- Estatísticas gerais
- Análise por confiança
- Análise por horário
- Análise por indicador
- Correlações
"""

import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

class BacktestAnalyzer:
    """Analisador de resultados de backtesting"""
    
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.df = None
        self.symbol = os.path.basename(csv_file).split('_')[2].replace('.csv', '')
    
    def load_data(self):
        """Carregar dados do CSV"""
        try:
            self.df = pd.read_csv(self.csv_file)
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            self.df['date'] = self.df['timestamp'].dt.date
            self.df['hour'] = self.df['timestamp'].dt.hour
            self.df['hit'] = self.df['hit'].astype(int)
            self.df['confidence'] = pd.to_numeric(self.df['confidence'], errors='coerce')
            
            print(f"✅ Dados carregados: {len(self.df)} registros")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar CSV: {e}")
            return False
    
    def print_general_stats(self):
        """Estatísticas gerais"""
        print("\n" + "="*80)
        print("📊 ESTATÍSTICAS GERAIS")
        print("="*80)
        
        total_days = len(self.df)
        total_hits = self.df['hit'].sum()
        hit_rate = (total_hits / total_days * 100) if total_days > 0 else 0
        
        print(f"\nTotal de dias analisados: {total_days}")
        print(f"Total de acertos: {total_hits}")
        print(f"Taxa de acerto: {hit_rate:.2f}%")
        print(f"\nConfiança:")
        print(f"  Média: {self.df['confidence'].mean():.4f} ({self.df['confidence'].mean()*100:.2f}%)")
        print(f"  Min: {self.df['confidence'].min():.4f}")
        print(f"  Max: {self.df['confidence'].max():.4f}")
        print(f"  Desvio padrão: {self.df['confidence'].std():.4f}")
        
        print(f"\nPips reais (movimento real):")
        print(f"  Média: {self.df['pips_actual'].mean():.2f}p")
        print(f"  Mediana: {self.df['pips_actual'].median():.2f}p")
        print(f"  Min: {self.df['pips_actual'].min():.2f}p")
        print(f"  Max: {self.df['pips_actual'].max():.2f}p")
        
        print(f"\nErro de previsão de preço:")
        print(f"  Média: {self.df['price_error_pct'].mean():.3f}%")
        print(f"  Mediana: {self.df['price_error_pct'].median():.3f}%")
        print(f"  Min: {self.df['price_error_pct'].min():.3f}%")
        print(f"  Max: {self.df['price_error_pct'].max():.3f}%")
    
    def print_confidence_analysis(self):
        """Análise por nível de confiança"""
        print("\n" + "="*80)
        print("🎯 ANÁLISE POR CONFIANÇA")
        print("="*80)
        
        conf_ranges = [
            (0.90, 1.00, "Very High (90-100%)"),
            (0.80, 0.90, "High (80-90%)"),
            (0.70, 0.80, "Medium-High (70-80%)"),
            (0.60, 0.70, "Medium (60-70%)"),
            (0.50, 0.60, "Low (50-60%)"),
            (0.0, 0.50, "Very Low (<50%)")
        ]
        
        print(f"\n{'Confiança':<25} {'Dias':<8} {'Acertos':<10} {'Taxa':<10} {'Pips Médio':<12}")
        print("-" * 65)
        
        for min_conf, max_conf, label in conf_ranges:
            mask = (self.df['confidence'] >= min_conf) & (self.df['confidence'] < max_conf)
            subset = self.df[mask]
            
            if len(subset) > 0:
                hits = subset['hit'].sum()
                rate = (hits / len(subset) * 100) if len(subset) > 0 else 0
                avg_pips = subset['pips_actual'].mean()
                
                print(f"{label:<25} {len(subset):<8} {hits:<10} {rate:>6.1f}% {avg_pips:>10.1f}p")
    
    def print_time_analysis(self):
        """Análise por horário"""
        print("\n" + "="*80)
        print("⏰ ANÁLISE POR HORÁRIO DO CANDLE")
        print("="*80)
        
        hourly = self.df.groupby('hour').agg({
            'hit': ['count', 'sum'],
            'confidence': 'mean',
            'pips_actual': 'mean',
            'price_error_pct': 'mean'
        }).round(4)
        
        print(f"\n{'Hora':<6} {'Dias':<8} {'Acertos':<10} {'Taxa':<10} {'Conf Med':<12} {'Pips Med':<12} {'Erro %':<10}")
        print("-" * 80)
        
        for hour in sorted(self.df['hour'].unique()):
            subset = self.df[self.df['hour'] == hour]
            hits = subset['hit'].sum()
            rate = (hits / len(subset) * 100) if len(subset) > 0 else 0
            avg_conf = subset['confidence'].mean()
            avg_pips = subset['pips_actual'].mean()
            avg_error = subset['price_error_pct'].mean()
            
            marker = "📈" if rate > 55 else "📊" if rate > 50 else "📉"
            print(f"{hour:<6} {len(subset):<8} {hits:<10} {rate:>6.1f}% {avg_conf:>10.2f}% {avg_pips:>10.1f}p {avg_error:>8.2f}% {marker}")
    
    def print_indicator_analysis(self):
        """Análise de indicadores para previsões corretas vs incorretas"""
        print("\n" + "="*80)
        print("📈 ANÁLISE DE INDICADORES (Acertos vs Erros)")
        print("="*80)
        
        hits = self.df[self.df['hit'] == 1]
        misses = self.df[self.df['hit'] == 0]
        
        indicators = ['rsi', 'sma_20', 'sma_50', 'atr', 'momentum', 'distance_std', 'volume_ratio']
        
        print(f"\n{'Indicador':<18} {'Acertos (Média)':<20} {'Erros (Média)':<20} {'Diferença':<15}")
        print("-" * 73)
        
        for ind in indicators:
            if ind in self.df.columns:
                hit_mean = hits[ind].mean()
                miss_mean = misses[ind].mean()
                diff = hit_mean - miss_mean
                
                marker = "✅" if abs(diff) > 0.5 else "⚠️ "
                print(f"{ind:<18} {hit_mean:>18.4f} {miss_mean:>20.4f} {diff:>13.4f} {marker}")
    
    def print_top_performers(self):
        """Mostrar melhores e piores previsões"""
        print("\n" + "="*80)
        print("🏆 MELHORES E PIORES PREVISÕES")
        print("="*80)
        
        # Melhores (acertos com alta confiança)
        print(f"\n✅ TOP 5 ACERTOS (Alta confiança + acerto):")
        print("-" * 80)
        top_hits = self.df[(self.df['hit'] == 1) & (self.df['confidence'] > 0.70)].nlargest(5, 'confidence')[
            ['date', 'time', 'close', 'confidence', 'predicted_direction', 'pips_actual']
        ]
        for idx, row in top_hits.iterrows():
            print(f"  {row['date']} {row['time']:<8} | Conf: {row['confidence']*100:>5.1f}% | {row['predicted_direction']} | Pips: {row['pips_actual']:>6.1f}p | Close: {row['close']:.5f}")
        
        # Piores (erros com alta confiança)
        print(f"\n❌ TOP 5 FALHAS (Alta confiança + erro):")
        print("-" * 80)
        top_misses = self.df[(self.df['hit'] == 0) & (self.df['confidence'] > 0.70)].nlargest(5, 'confidence')[
            ['date', 'time', 'close', 'confidence', 'predicted_direction', 'actual_direction', 'pips_actual']
        ]
        for idx, row in top_misses.iterrows():
            print(f"  {row['date']} {row['time']:<8} | Conf: {row['confidence']*100:>5.1f}% | Previsto: {row['predicted_direction']:<4} Real: {row['actual_direction']} | Pips: {row['pips_actual']:>6.1f}p")
    
    def print_direction_analysis(self):
        """Análise de direções (UP vs DOWN)"""
        print("\n" + "="*80)
        print("📊 ANÁLISE DE DIREÇÕES (UP vs DOWN)")
        print("="*80)
        
        up_preds = self.df[self.df['predicted_direction'] == 'UP']
        down_preds = self.df[self.df['predicted_direction'] == 'DOWN']
        
        up_hits = up_preds['hit'].sum()
        down_hits = down_preds['hit'].sum()
        
        up_rate = (up_hits / len(up_preds) * 100) if len(up_preds) > 0 else 0
        down_rate = (down_hits / len(down_preds) * 100) if len(down_preds) > 0 else 0
        
        print(f"\nPrevisões UP:")
        print(f"  Total: {len(up_preds)}")
        print(f"  Acertos: {up_hits}")
        print(f"  Taxa: {up_rate:.2f}%")
        print(f"  Confiança média: {up_preds['confidence'].mean()*100:.2f}%")
        
        print(f"\nPrevisões DOWN:")
        print(f"  Total: {len(down_preds)}")
        print(f"  Acertos: {down_hits}")
        print(f"  Taxa: {down_rate:.2f}%")
        print(f"  Confiança média: {down_preds['confidence'].mean()*100:.2f}%")
    
    def save_analysis_report(self, output_file=None):
        """Salvar análise em arquivo texto"""
        if output_file is None:
            output_file = f"/tmp/backtest_analysis_{self.symbol}.txt"
        
        try:
            with open(output_file, 'w') as f:
                # Redirecionar prints para arquivo
                import io
                from contextlib import redirect_stdout
                
                # Fazer análises e escrever
                f.write(f"ANÁLISE DE BACKTESTING - {self.symbol}\n")
                f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Arquivo: {self.csv_file}\n")
                f.write("="*80 + "\n\n")
                
                # Estatísticas gerais (capturar print)
                f.write("ESTATÍSTICAS GERAIS\n")
                f.write("="*80 + "\n")
                total_days = len(self.df)
                total_hits = self.df['hit'].sum()
                hit_rate = (total_hits / total_days * 100) if total_days > 0 else 0
                f.write(f"Total de dias: {total_days}\n")
                f.write(f"Acertos: {total_hits}\n")
                f.write(f"Taxa: {hit_rate:.2f}%\n\n")
            
            print(f"✅ Análise salva em: {output_file}")
            return output_file
        
        except Exception as e:
            print(f"❌ Erro ao salvar análise: {e}")
            return None


def main():
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*20 + "📊 ANÁLISE DE RESULTADOS DE BACKTESTING" + " "*20 + "║")
    print("╚" + "="*78 + "╝")
    
    # Detectar arquivo CSV
    csv_files = []
    for f in os.listdir("/tmp"):
        if f.startswith("backtest_results_") and f.endswith(".csv"):
            csv_files.append(f"/tmp/{f}")
    
    if not csv_files:
        print("\n❌ Nenhum arquivo de backtesting encontrado em /tmp/")
        print("\nPrimeiro, execute o backtesting:")
        print("  bash /home/ubuntu/pessoal/options/bin/backtest_master.sh")
        print("  Escolha opção 1")
        return
    
    # Analisar cada arquivo
    for csv_file in sorted(csv_files):
        analyzer = BacktestAnalyzer(csv_file)
        
        if analyzer.load_data():
            analyzer.print_general_stats()
            analyzer.print_confidence_analysis()
            analyzer.print_time_analysis()
            analyzer.print_indicator_analysis()
            analyzer.print_direction_analysis()
            analyzer.print_top_performers()
            analyzer.save_analysis_report()


if __name__ == '__main__':
    main()
