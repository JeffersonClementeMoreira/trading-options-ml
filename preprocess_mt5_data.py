#!/usr/bin/env python3
"""
Preprocessor para dados MT5

Converte formato MT5 (espaços) para CSV padrão
"""

import pandas as pd
import sys
from pathlib import Path


def preprocess_mt5_csv(input_path: str, output_path: str = None):
    """
    Converte CSV MT5 para formato padrão com datetime index.
    
    Entrada:
        <DATE>  <TIME>  <OPEN>  <HIGH>  <LOW>   <CLOSE> <TICKVOL>       <VOL>   <SPREAD>
        2023.01.01      22:00:00        1.06971 1.07070 1.06860 1.06888 70      0      7
        
    Saída:
        datetime,open,high,low,close,volume,tickvol,spread
        2023-01-01 22:00:00,1.06971,1.07070,1.06860,1.06888,0,70,7
    """
    
    print(f"📂 Lendo arquivo MT5: {input_path}")
    
    # Ler arquivo com espaços como separador (usar regex)
    df = pd.read_csv(input_path, sep=r'\s+', skiprows=1, engine='python')
    
    print(f"✅ Carregado com {len(df)} linhas")
    print(f"   Colunas: {list(df.columns)}")
    
    # Renomear primeira coluna (é DATE)
    df.columns = ['date', 'time', 'open', 'high', 'low', 'close', 'tickvol', 'volume', 'spread']
    
    # Combinar DATE e TIME em datetime
    df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str), 
                                    format='%Y.%m.%d %H:%M:%S')
    
    # Selecionar apenas colunas necessárias
    df_clean = df[['datetime', 'open', 'high', 'low', 'close', 'volume', 'tickvol', 'spread']].copy()
    
    # Ordenar por datetime
    df_clean = df_clean.sort_values('datetime').reset_index(drop=True)
    
    print(f"\n📊 Dados processados:")
    print(f"   Período: {df_clean['datetime'].min()} a {df_clean['datetime'].max()}")
    print(f"   Total: {len(df_clean)} candles")
    print(f"   Candles/dia: {len(df_clean) / ((df_clean['datetime'].max() - df_clean['datetime'].min()).days + 1):.0f}")
    
    # Salvar
    if output_path is None:
        base = Path(input_path).stem
        output_path = str(Path(input_path).parent / f"{base}_processed.csv")
    
    df_clean.to_csv(output_path, index=False)
    print(f"\n✅ Salvo em: {output_path}")
    
    return df_clean


def main():
    input_file = '/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015.csv'
    
    if not Path(input_file).exists():
        print(f"❌ Arquivo não encontrado: {input_file}")
        return 1
    
    df = preprocess_mt5_csv(input_file)
    
    # Mostrar amostra
    print("\n📋 Amostra dos dados:")
    print(df.head())
    print(df.tail())
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
