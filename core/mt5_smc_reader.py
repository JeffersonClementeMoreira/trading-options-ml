"""
MT5 SMC Features Reader - Lê features calculadas pelo indicador MQ5.

Workflow:
1. Indicador MQ5 roda no MT5 e calcula 25+ features SMC
2. Exporta para arquivo CSV: smc_features.csv
3. Este módulo lê o arquivo e retorna as features
4. XGBoost usa essas features para prever

Vantagens:
- SMC roda em tempo real no MT5 (sem latência)
- Python consome dados já prontos
- Evita duplicação de cálculos
- Sincronização perfeita com preços do MT5
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple


class MT5SMCFeaturesReader:
    """Lê features SMC exportadas pelo indicador MT5."""
    
    def __init__(self, smc_csv_path: Optional[Path] = None):
        """
        Args:
            smc_csv_path: Caminho para smc_features.csv (exportado pelo MT5)
                         Se None, procura em ~/Downloads/smc_features.csv
        """
        if smc_csv_path is None:
            # Procurar em locais comuns
            possible_paths = [
                Path.home() / "Downloads" / "smc_features.csv",
                Path("/home/ubuntu/pessoal/options/dados/smc_features.csv"),
                Path("/home/ubuntu/Downloads/smc_features.csv"),
            ]
            
            self.smc_csv_path = None
            for p in possible_paths:
                if p.exists():
                    self.smc_csv_path = p
                    break
            
            if self.smc_csv_path is None:
                print("WARNING: smc_features.csv não encontrado")
                self.smc_csv_path = possible_paths[0]
        else:
            self.smc_csv_path = Path(smc_csv_path)
        
        self.df = None
        self.last_update = None
    
    def load(self) -> bool:
        """
        Carrega dados do arquivo CSV.
        
        Returns:
            True se carregou com sucesso, False caso contrário
        """
        if not self.smc_csv_path.exists():
            print(f"ERROR: {self.smc_csv_path} não encontrado")
            return False
        
        try:
            self.df = pd.read_csv(self.smc_csv_path, sep='\t')
            self.last_update = datetime.now()
            print(f"✅ Carregados {len(self.df)} linhas de features SMC")
            return True
        except Exception as e:
            print(f"ERROR ao ler {self.smc_csv_path}: {e}")
            return False
    
    def reload_if_updated(self) -> bool:
        """
        Recarrega arquivo se foi atualizado desde a última leitura.
        
        Returns:
            True se recarregou, False caso contrário
        """
        if not self.smc_csv_path.exists():
            return False
        
        file_mtime = self.smc_csv_path.stat().st_mtime
        if self.last_update is None:
            return self.load()
        
        file_datetime = datetime.fromtimestamp(file_mtime)
        if file_datetime > self.last_update:
            print("📁 smc_features.csv atualizado, recarregando...")
            return self.load()
        
        return False
    
    def get_latest_features(self) -> Optional[Dict]:
        """
        Retorna features SMC da última linha (candle mais recente).
        
        Returns:
            Dict com todas as 25+ features, ou None se erro
        """
        if self.df is None or len(self.df) == 0:
            return None
        
        latest_row = self.df.iloc[-1]
        
        return {
            'datetime': latest_row.get('datetime'),
            'dist_top_liquidity': float(latest_row.get('dist_top_liquidity', 0)),
            'dist_bottom_liquidity': float(latest_row.get('dist_bottom_liquidity', 0)),
            'sweep_top_count': float(latest_row.get('sweep_top_count', 0)),
            'sweep_bottom_count': float(latest_row.get('sweep_bottom_count', 0)),
            'sweep_imbalance': float(latest_row.get('sweep_imbalance', 0)),
            'bos_bull_count': float(latest_row.get('bos_bull_count', 0)),
            'bos_bear_count': float(latest_row.get('bos_bear_count', 0)),
            'bos_ratio': float(latest_row.get('bos_ratio', 0)),
            'candles_since_choch': float(latest_row.get('candles_since_choch', 0)),
            'choch_type': float(latest_row.get('choch_type', 0)),
            'bull_fvg_count': float(latest_row.get('bull_fvg_count', 0)),
            'bear_fvg_count': float(latest_row.get('bear_fvg_count', 0)),
            'fvg_pressure': float(latest_row.get('fvg_pressure', 0)),
            'mean_displacement': float(latest_row.get('mean_displacement', 0)),
            'max_displacement': float(latest_row.get('max_displacement', 0)),
            'displacement_efficiency': float(latest_row.get('displacement_efficiency', 0)),
            'premium_position': float(latest_row.get('premium_position', 0)),
            'premium_discount_score': float(latest_row.get('premium_discount_score', 0)),
            'atr_compression_ratio': float(latest_row.get('atr_compression_ratio', 0)),
            'vol_regime': float(latest_row.get('vol_regime', 0)),
            'liquidity_void_score': float(latest_row.get('liquidity_void_score', 0)),
            'stop_hunt_prob': float(latest_row.get('stop_hunt_prob', 0)),
            'trend_duration': float(latest_row.get('trend_duration', 0)),
            'range_duration': float(latest_row.get('range_duration', 0)),
            'regime_strength': float(latest_row.get('regime_strength', 0)),
        }
    
    def get_features_for_datetime(self, target_datetime: str) -> Optional[Dict]:
        """
        Retorna features SMC para um datetime específico.
        
        Args:
            target_datetime: String no formato "YYYY-MM-DD HH:MM:SS"
        
        Returns:
            Dict com features, ou None se não encontrado
        """
        if self.df is None or len(self.df) == 0:
            return None
        
        # Procurar linha com datetime matching
        matching = self.df[self.df['datetime'] == target_datetime]
        
        if matching.empty:
            return None
        
        row = matching.iloc[0]
        return self._row_to_dict(row)
    
    def get_all_features_df(self) -> Optional[pd.DataFrame]:
        """
        Retorna DataFrame completo com todas as features.
        
        Returns:
            DataFrame ou None
        """
        if self.df is None:
            return None
        
        return self.df.copy()
    
    def _row_to_dict(self, row) -> Dict:
        """Converte uma linha do DataFrame para dict de features."""
        return {
            'datetime': row.get('datetime'),
            'dist_top_liquidity': float(row.get('dist_top_liquidity', 0)),
            'dist_bottom_liquidity': float(row.get('dist_bottom_liquidity', 0)),
            'sweep_top_count': float(row.get('sweep_top_count', 0)),
            'sweep_bottom_count': float(row.get('sweep_bottom_count', 0)),
            'sweep_imbalance': float(row.get('sweep_imbalance', 0)),
            'bos_bull_count': float(row.get('bos_bull_count', 0)),
            'bos_bear_count': float(row.get('bos_bear_count', 0)),
            'bos_ratio': float(row.get('bos_ratio', 0)),
            'candles_since_choch': float(row.get('candles_since_choch', 0)),
            'choch_type': float(row.get('choch_type', 0)),
            'bull_fvg_count': float(row.get('bull_fvg_count', 0)),
            'bear_fvg_count': float(row.get('bear_fvg_count', 0)),
            'fvg_pressure': float(row.get('fvg_pressure', 0)),
            'mean_displacement': float(row.get('mean_displacement', 0)),
            'max_displacement': float(row.get('max_displacement', 0)),
            'displacement_efficiency': float(row.get('displacement_efficiency', 0)),
            'premium_position': float(row.get('premium_position', 0)),
            'premium_discount_score': float(row.get('premium_discount_score', 0)),
            'atr_compression_ratio': float(row.get('atr_compression_ratio', 0)),
            'vol_regime': float(row.get('vol_regime', 0)),
            'liquidity_void_score': float(row.get('liquidity_void_score', 0)),
            'stop_hunt_prob': float(row.get('stop_hunt_prob', 0)),
            'trend_duration': float(row.get('trend_duration', 0)),
            'range_duration': float(row.get('range_duration', 0)),
            'regime_strength': float(row.get('regime_strength', 0)),
        }


class SMCFeaturesIntegration:
    """Integração entre MT5 (que gera features) e XGBoost (que as consome)."""
    
    def __init__(self, smc_csv_path: Optional[Path] = None):
        self.reader = MT5SMCFeaturesReader(smc_csv_path)
        self.ready = False
    
    def initialize(self) -> bool:
        """
        Inicializa o leitor de features.
        
        Returns:
            True se conseguiu carregar features
        """
        success = self.reader.load()
        self.ready = success
        return success
    
    def update(self) -> bool:
        """
        Verifica se há atualizações e recarrega se necessário.
        
        Returns:
            True se houve atualização
        """
        return self.reader.reload_if_updated()
    
    def get_current_features(self) -> Optional[Dict]:
        """Retorna features do candle atual (último da série)."""
        if not self.ready:
            return None
        
        return self.reader.get_latest_features()
    
    def get_features_df(self) -> Optional[pd.DataFrame]:
        """Retorna DataFrame completo para treinamento."""
        if not self.ready:
            return None
        
        return self.reader.get_all_features_df()


# ===== EXEMPLO DE USO =====

if __name__ == "__main__":
    print("\n" + "="*80)
    print("📊 MT5 SMC FEATURES READER - Example Usage")
    print("="*80 + "\n")
    
    # Opção 1: Usar path automático
    reader = MT5SMCFeaturesReader()
    
    if reader.load():
        print("✅ Features carregadas com sucesso\n")
        
        # Obter últimas features
        latest = reader.get_latest_features()
        if latest:
            print("📌 Latest Features:")
            print(f"  DateTime: {latest['datetime']}")
            print(f"  Distance to Top: {latest['dist_top_liquidity']:.2f} ATRs")
            print(f"  Distance to Bottom: {latest['dist_bottom_liquidity']:.2f} ATRs")
            print(f"  Sweep Imbalance: {latest['sweep_imbalance']:.3f}")
            print(f"  Premium Position: {latest['premium_position']:.2f}")
            print(f"  ATR Compression: {latest['atr_compression_ratio']:.3f}")
            print(f"  FVG Pressure: {latest['fvg_pressure']:.3f}")
            print()
        
        # Obter DataFrame completo
        df = reader.get_all_features_df()
        if df is not None:
            print(f"📈 Total de candles: {len(df)}")
            print(f"📊 Features disponíveis: {len(df.columns)}")
            print("\nPrimeiras 3 linhas:")
            print(df.head(3))
    else:
        print("❌ Não foi possível carregar features")
