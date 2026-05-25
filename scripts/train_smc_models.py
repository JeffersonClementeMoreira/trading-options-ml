#!/usr/bin/env python3
"""
Example: Train all SMC XGBoost models with your EURUSD data.

Usage:
    python3 train_smc_models.py --data dados/EURUSD_M15_*.csv
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np

from core.indicators import build_indicators
from core.smc import calculate_extremes
from core.smc_features import generate_all_smc_features
from core.smc_xgboost import SMCXGBoostTrainer


def load_and_prepare_data(csv_file: Path) -> tuple:
    """Load MT5 CSV and prepare for modeling."""
    
    print(f"Loading data from: {csv_file}")
    
    # Load CSV
    df = pd.read_csv(csv_file, sep="\t")
    
    # Clean column names
    df.columns = [col.strip().lower().replace("<", "").replace(">", "") for col in df.columns]
    
    # Create datetime
    df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], errors="coerce")
    df = df.set_index("datetime").sort_index()
    
    # Convert to numeric
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Fill volume if missing
    if "volume" not in df.columns:
        df["volume"] = 1
    else:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(1)
    
    # Remove rows with NaN prices
    df = df.dropna(subset=["open", "high", "low", "close"])
    
    print(f"  Loaded {len(df)} candles")
    print(f"  Date range: {df.index.min()} to {df.index.max()}")
    
    # Build indicators
    print("Building indicators...")
    df = build_indicators(df)
    
    # Calculate SMC extremes
    print("Detecting SMC extremes...")
    extremos = calculate_extremes(df)
    print(f"  Found {len(extremos)} extremes (tops + bottoms)")
    
    # Generate SMC features
    print("Generating SMC features (25+ continuous features)...")
    smc_features = generate_all_smc_features(df, extremos)
    
    print(f"  Generated {len(smc_features.columns)} SMC features")
    print(f"  Features: {', '.join(smc_features.columns[:5])}...")
    
    return df, smc_features, extremos


def main():
    parser = argparse.ArgumentParser(description="Train SMC XGBoost models")
    parser.add_argument("--data", type=str, help="Path to CSV file", 
                       default="/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015.csv")
    parser.add_argument("--output", type=str, help="Output directory for models",
                       default="/home/ubuntu/pessoal/options/models")
    
    args = parser.parse_args()
    
    csv_file = Path(args.data)
    if not csv_file.exists():
        print(f"ERROR: File not found: {csv_file}")
        return 1
    
    # Load and prepare data
    df, smc_features, extremos = load_and_prepare_data(csv_file)
    
    # Train models
    trainer = SMCXGBoostTrainer(output_dir=Path(args.output))
    trainer.train_all(df, smc_features, extremos)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
