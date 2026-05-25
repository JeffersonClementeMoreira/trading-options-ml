"""
Daily Backtester with Multi-Timeframe Confluence

Roda análise dia-a-dia e salva:
1. Sugestão de trade por dia
2. Análises (M15, H4, confluência)
3. Resultado do fechamento do dia seguinte
4. Tudo em CSV para visualização
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys

# Adicionar path para imports
sys.path.insert(0, '/home/ubuntu/pessoal/options')

from core.multi_timeframe_confluence import MultiTimeframeConfluence
from core.enhanced_features import generate_enhanced_features


class DailyBacktester:
    """Backtester que roda dia-a-dia com confluência de TF."""
    
    def __init__(self, data_path: str, model_path: Optional[str] = None, output_dir: str = 'backtest_results'):
        """
        Args:
            data_path: Caminho para CSV com dados M15
            model_path: Caminho para modelo XGBoost treinado
            output_dir: Diretório para salvar resultados
        """
        self.data_path = data_path
        self.model_path = model_path
        self.output_dir = output_dir
        self.confluence = MultiTimeframeConfluence(verbose=False)
        
        # Criar diretório de output
        Path(output_dir).mkdir(exist_ok=True)
        
        # Carregar dados
        print(f"📊 Carregando dados de {data_path}...")
        self.df = pd.read_csv(data_path)
        
        # Converter coluna datetime se existe
        if 'datetime' in self.df.columns:
            self.df['datetime'] = pd.to_datetime(self.df['datetime'])
            self.df.set_index('datetime', inplace=True)
        elif 'time' in self.df.columns:
            self.df['time'] = pd.to_datetime(self.df['time'])
            self.df.set_index('time', inplace=True)
        else:
            # Tentar primeira coluna numérica ou index padrão
            self.df.index = pd.to_datetime(self.df.index)
        
        # Garantir que está ordenado por data
        self.df = self.df.sort_index()
        
        print(f"✅ Dados carregados: {len(self.df)} candles")
        print(f"   Período: {self.df.index[0]} a {self.df.index[-1]}")
        
        # Carregar modelo XGBoost se disponível
        if model_path and os.path.exists(model_path):
            import pickle
            try:
                with open(model_path, 'rb') as f:
                    self.xgb_model = pickle.load(f)
                print(f"✅ Modelo XGBoost carregado")
            except:
                print(f"⚠️ Erro ao carregar modelo XGBoost")
                self.xgb_model = None
        else:
            self.xgb_model = None
            print("⚠️ Modelo XGBoost não disponível (usará tendência técnica)")
        
        # Resultados
        self.daily_results = []
    
    def get_day_data(self, date: datetime) -> Optional[pd.DataFrame]:
        """Obtém dados do dia específico (até 23:59 do dia anterior)."""
        
        # Filtrar dados até fim do dia anterior
        next_day = date + timedelta(days=1)
        day_data = self.df[(self.df.index.date >= date.date()) & (self.df.index.date < next_day.date())]
        
        if len(day_data) < 20:  # Mínimo de candles para análise
            return None
        
        return day_data
    
    def get_next_day_close(self, date: datetime) -> Optional[float]:
        """Obtém fechamento do dia seguinte."""
        
        next_day = date + timedelta(days=1)
        next_day_end = next_day + timedelta(days=1)
        
        next_day_data = self.df[(self.df.index.date >= next_day.date()) & (self.df.index.date < next_day_end.date())]
        
        if len(next_day_data) == 0:
            return None
        
        return next_day_data['close'].iloc[-1]
    
    def get_xgboost_prediction(self, df_day: pd.DataFrame) -> Tuple[int, float]:
        """
        Obtém previsão do XGBoost para o dia.
        Usa a última linha de dados disponível no dia.
        
        Returns:
            (prediction, probability)
        """
        
        if self.xgb_model is None:
            return None, None
        
        try:
            # Gerar features para última vela do dia
            df_features = generate_enhanced_features(df_day.copy())
            
            if len(df_features) == 0:
                return None, None
            
            # Usar última linha
            X = df_features.iloc[-1:].fillna(0)
            
            # Predição
            pred = self.xgb_model.predict(X)[0]
            prob = self.xgb_model.predict_proba(X)[0]
            
            # Retornar classe e probabilidade da classe predita
            if pred == 1:
                return 1, prob[1]
            else:
                return 0, prob[0]
        
        except Exception as e:
            print(f"⚠️ Erro ao gerar predição XGBoost: {e}")
            return None, None
    
    def get_technical_prediction(self, df_day: pd.DataFrame) -> Tuple[int, float]:
        """
        Obtém previsão apenas por análise técnica (sem XGBoost).
        
        Baseado em:
        - SMA alignment
        - Momentum
        - Price vs MA200
        """
        
        if len(df_day) < 50:  # Reduzir para 50 (menos de 1 dia completo)
            return None, None
        
        # Usar window menores se não temos 200 candles
        sma_period_long = min(200, len(df_day) // 2)
        sma_period_med = min(50, len(df_day) // 4)
        sma_period_short = min(20, len(df_day) // 8)
        
        sma_short = df_day['close'].rolling(sma_period_short).mean().iloc[-1]
        sma_med = df_day['close'].rolling(sma_period_med).mean().iloc[-1]
        sma_long = df_day['close'].rolling(sma_period_long).mean().iloc[-1]
        
        current_price = df_day['close'].iloc[-1]
        
        # Momentum
        momentum_10 = (df_day['close'].iloc[-1] - df_day['close'].iloc[-10]) / df_day['close'].iloc[-10] if len(df_day) >= 10 else 0
        
        # Score
        score = 0
        if sma_short > sma_med:
            score += 1
        if sma_med > sma_long:
            score += 1
        if current_price > sma_long:
            score += 1
        if momentum_10 > 0:
            score += 1
        
        # Predição (3+ de 4 indica tendência)
        if score >= 3:
            pred = 1  # UP
            prob = 0.5 + (score * 0.1)  # 0.6 a 0.8
        elif score <= 1:
            pred = 0  # DOWN
            prob = 0.5 + ((4 - score) * 0.1)  # 0.6 a 0.8
        else:
            pred = 1 if sma_short > sma_med else 0
            prob = 0.55
        
        return pred, min(0.99, prob)
    
    def analyze_day(self, date: datetime) -> Optional[Dict]:
        """
        Analisa um dia específico e retorna resultado.
        """
        
        # Obter dados do dia
        day_data = self.get_day_data(date)
        if day_data is None or len(day_data) == 0:
            return None
        
        # Obter previsão XGBoost ou técnica
        if self.xgb_model:
            xgb_pred, xgb_prob = self.get_xgboost_prediction(day_data)
        else:
            xgb_pred, xgb_prob = self.get_technical_prediction(day_data)
            if xgb_pred is None:
                return None
        
        # Analisar confluência
        confluence = self.confluence.analyze_confluence(day_data)
        
        # Ajustar previsão com confluência
        pred_adjusted, prob_adjusted, confluence_reasoning = self.confluence.adjust_prediction_with_confluence(
            xgb_pred, xgb_prob, day_data
        )
        
        # Obter fechamento do dia seguinte
        next_day_close = self.get_next_day_close(date)
        current_close = day_data['close'].iloc[-1]
        
        if next_day_close is None:
            result_status = "NO_DATA"
            result_pct = None
            was_correct = None
        else:
            change_pct = (next_day_close - current_close) / current_close
            result_pct = change_pct
            
            # Verificar se acertou
            if pred_adjusted == 1:
                was_correct = change_pct > 0
            else:
                was_correct = change_pct < 0
            
            result_status = "UP" if change_pct > 0 else "DOWN"
        
        result = {
            'date': date.strftime('%Y-%m-%d'),
            'day_of_week': date.strftime('%A'),
            
            # Previsões
            'xgb_pred': 'UP' if xgb_pred == 1 else 'DOWN',
            'xgb_prob': f"{xgb_prob:.1%}" if xgb_prob else "N/A",
            
            # Confluência
            'm15_trend': confluence.m15_trend,
            'h4_trend': confluence.h4_trend,
            'is_aligned': '✅' if confluence.is_aligned else '❌',
            'alignment_score': f"{confluence.alignment_score:.0%}",
            'confidence_adjustment': f"{confluence.confidence_adjustment:+.0%}",
            
            # Previsão ajustada
            'final_pred': 'UP' if pred_adjusted == 1 else 'DOWN',
            'final_prob': f"{prob_adjusted:.1%}",
            
            # Resultado
            'result': result_status,
            'change_pct': f"{result_pct:.2%}" if result_pct else "N/A",
            'was_correct': '✅' if was_correct else ('❌' if was_correct is not None else 'WAIT'),
            
            # Detalhes
            'current_close': f"{current_close:.5f}",
            'next_close': f"{next_day_close:.5f}" if next_day_close else "N/A",
            
            'reasoning': confluence_reasoning,
        }
        
        return result
    
    def run_backtest(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Roda backtest para período específico.
        
        Args:
            start_date: Data inicial (formato 'YYYY-MM-DD')
            end_date: Data final (formato 'YYYY-MM-DD')
        """
        
        # Obter datas
        if start_date:
            start_dt = pd.to_datetime(start_date)
        else:
            start_dt = self.df.index[0]
        
        if end_date:
            end_dt = pd.to_datetime(end_date)
        else:
            end_dt = self.df.index[-1]
        
        print(f"\n🚀 Iniciando backtest: {start_dt.date()} a {end_dt.date()}\n")
        
        # Obter datas únicas do arquivo (não gerar todas as datas)
        # Isso evita problemas com fins de semana/feriados sem dados
        unique_dates = self.df.index.normalize().unique()
        unique_dates = pd.DatetimeIndex(unique_dates).sort_values()
        
        # Filtrar para período
        unique_dates = unique_dates[(unique_dates >= start_dt) & (unique_dates <= end_dt)]
        
        for date_ts in unique_dates:
            date = date_ts.to_pydatetime()
            result = self.analyze_day(date)
            
            if result:
                self.daily_results.append(result)
                
                # Mostrar resultado
                status_emoji = '✅' if result['was_correct'] == '✅' else ('❌' if result['was_correct'] == '❌' else '⏳')
                print(f"{status_emoji} {result['date']} | "
                      f"Pred: {result['final_pred']} ({result['final_prob']}) | "
                      f"M15: {result['m15_trend']} H4: {result['h4_trend']} ({result['alignment_score']}) | "
                      f"Resultado: {result['result']} ({result['change_pct']}) | "
                      f"Acerto: {result['was_correct']}")
        
        print(f"\n✅ Backtest finalizado com {len(self.daily_results)} dias analisados\n")
    
    def save_results_to_csv(self, filename: Optional[str] = None):
        """Salva resultados em CSV."""
        
        if not self.daily_results:
            print("⚠️ Nenhum resultado para salvar")
            return
        
        if filename is None:
            filename = f"{self.output_dir}/backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        df_results = pd.DataFrame(self.daily_results)
        df_results.to_csv(filename, index=False)
        
        print(f"✅ Resultados salvos em: {filename}")
        
        # Mostrar estatísticas
        self.print_statistics(df_results)
        
        return filename
    
    def print_statistics(self, df_results: pd.DataFrame):
        """Imprime estatísticas dos resultados."""
        
        # Filtrar apenas dias com resultado
        df_valid = df_results[df_results['was_correct'].isin(['✅', '❌'])].copy()
        
        if len(df_valid) == 0:
            print("⚠️ Sem dados válidos para análise")
            return
        
        total_trades = len(df_valid)
        correct_trades = len(df_valid[df_valid['was_correct'] == '✅'])
        win_rate = correct_trades / total_trades if total_trades > 0 else 0
        
        # Confluência
        aligned_trades = len(df_valid[df_valid['is_aligned'] == '✅'])
        aligned_correct = len(df_valid[(df_valid['is_aligned'] == '✅') & (df_valid['was_correct'] == '✅')])
        aligned_win_rate = aligned_correct / aligned_trades if aligned_trades > 0 else 0
        
        divergent_trades = total_trades - aligned_trades
        divergent_correct = correct_trades - aligned_correct
        divergent_win_rate = divergent_correct / divergent_trades if divergent_trades > 0 else 0
        
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║              📊 BACKTEST STATISTICS                      ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  TOTAL:                                                   ║
║    Trades Analisados:        {total_trades:<5}                    ║
║    Acertos:                  {correct_trades:<5} ({win_rate:>6.1%})                ║
║    Erros:                    {total_trades - correct_trades:<5}                    ║
║                                                           ║
║  COM CONFLUÊNCIA (M15 = H4):                              ║
║    Trades:                   {aligned_trades:<5}                    ║
║    Acertos:                  {aligned_correct:<5} ({aligned_win_rate:>6.1%})                ║
║                                                           ║
║  SEM CONFLUÊNCIA (M15 ≠ H4):                              ║
║    Trades:                   {divergent_trades:<5}                    ║
║    Acertos:                  {divergent_correct:<5} ({divergent_win_rate:>6.1%})                ║
║                                                           ║
║  MELHORIA COM CONFLUÊNCIA:   {(aligned_win_rate - divergent_win_rate):+.1%}                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)
    
    def print_sample_results(self, n: int = 5):
        """Imprime N primeiros resultados."""
        
        if not self.daily_results:
            print("⚠️ Nenhum resultado")
            return
        
        print(f"\n📋 Primeiros {min(n, len(self.daily_results))} resultados:\n")
        
        for result in self.daily_results[:n]:
            print(f"{'='*80}")
            print(f"📅 {result['date']} ({result['day_of_week']})")
            print(f"")
            print(f"  🤖 XGBoost:        {result['xgb_pred']} ({result['xgb_prob']})")
            print(f"  📊 Tendência M15:  {result['m15_trend']}")
            print(f"  📊 Tendência H4:   {result['h4_trend']}")
            print(f"  🎯 Confluência:    {result['is_aligned']} (Score: {result['alignment_score']}, Ajuste: {result['confidence_adjustment']})")
            print(f"")
            print(f"  ✅ Previsão Final: {result['final_pred']} ({result['final_prob']})")
            print(f"  📈 Resultado:      {result['result']} ({result['change_pct']})")
            print(f"  🎯 Acertou:        {result['was_correct']}")
            print(f"")
            print(f"  💬 {result['reasoning']}")
            print()


def main():
    """Exemplo de uso."""
    
    # Definir caminhos
    data_path = '/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015.csv'
    model_path = '/home/ubuntu/pessoal/options/models/xgboost_model.pkl'
    
    # Criar backtester
    backtester = DailyBacktester(
        data_path=data_path,
        model_path=model_path,
        output_dir='backtest_results'
    )
    
    # Rodar backtest para últimos 30 dias
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    backtester.run_backtest(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    
    # Salvar resultados
    csv_file = backtester.save_results_to_csv()
    
    # Mostrar amostra
    backtester.print_sample_results(n=10)
    
    print(f"\n✅ CSV salvo em: {csv_file}")


if __name__ == '__main__':
    main()
