#!/usr/bin/env python3
"""
Multi-Model XGBoost Trainer using SMC Features.

Trains 5 specialized models:
1. Direction: Will next day close be UP or DOWN?
2. Sweep: Will there be a sweep in next 5 candles?
3. Reversal: Will price reverse after sweep?
4. Expected Move: What's the likely range for next day?
5. Strike Selection: Which strikes are likely to expire OTM?
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List
from pathlib import Path
import pickle

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("WARNING: XGBoost not installed. Install with: pip install xgboost")

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_absolute_error, r2_score


class SMCXGBoostTrainer:
    """Train multiple XGBoost models using SMC features."""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("/home/ubuntu/pessoal/options/models")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.models = {}
        self.scalers = {}
        self.feature_names = []
        
    def prepare_data(
        self,
        df: pd.DataFrame,
        smc_features: pd.DataFrame,
        target_shift: int = 1
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data with proper validation.
        
        Args:
            df: OHLCV dataframe
            smc_features: SMC features dataframe
            target_shift: Periods to shift target (1 = next day)
        
        Returns:
            features_df, target_series
        """
        # Combine features
        X = smc_features.copy()
        
        # Add technical indicators
        if "atr" in df.columns:
            X["atr"] = df["atr"]
        if "rsi" in df.columns:
            X["rsi"] = df["rsi"]
        
        # Add price features
        X["close"] = df["close"]
        X["high"] = df["high"]
        X["low"] = df["low"]
        X["volume"] = df["volume"] if "volume" in df.columns else 0
        X["return_pct"] = df["close"].pct_change() * 100
        
        # Create target: Next day close vs current close
        X["target_close"] = df["close"].shift(-target_shift)
        
        # Remove rows with NaN targets
        valid_idx = X["target_close"].notna()
        X = X[valid_idx].copy()
        
        # Target: 1 if UP, 0 if DOWN/FLAT
        y_direction = (X["target_close"] > X["close"]).astype(int)
        
        # Remove target from features
        X = X.drop(columns=["target_close", "close", "high", "low"])
        
        self.feature_names = X.columns.tolist()
        
        return X, y_direction
    
    def train_direction_model(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2
    ) -> Dict:
        """Train Model 1: Predict if price will go UP tomorrow."""
        
        print("\n" + "="*80)
        print("🎯 MODEL 1: DIRECTION PREDICTION")
        print("="*80)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False
        )
        
        # Train XGBoost
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="logloss"
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        print(f"Accuracy:  {accuracy:.1%}")
        print(f"Precision: {precision:.1%}")
        print(f"Recall:    {recall:.1%}")
        print(f"F1 Score:  {f1:.1%}")
        
        # Feature importance
        importances = model.feature_importances_
        top_features = sorted(zip(self.feature_names, importances), key=lambda x: x[1], reverse=True)[:5]
        print(f"\nTop 5 Important Features:")
        for feat, imp in top_features:
            print(f"  {feat}: {imp:.3f}")
        
        self.models["direction"] = model
        
        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1
        }
    
    def train_sweep_model(
        self,
        df: pd.DataFrame,
        X: pd.DataFrame,
        test_size: float = 0.2
    ) -> Dict:
        """Train Model 2: Will there be a sweep in next 5 candles?"""
        
        print("\n" + "="*80)
        print("🎯 MODEL 2: SWEEP PREDICTION")
        print("="*80)
        
        # Create target: 1 if there's a sweep in next 5 candles
        y_sweep = pd.Series(0, index=df.index)
        
        for i in range(len(df) - 5):
            future_5 = df.iloc[i:i+5]
            current_price = df["close"].iloc[i]
            
            # Sweep if price exceeds recent high/low by 2 ATR
            atr = df["atr"].iloc[i] if "atr" in df.columns else 1.0
            
            if (future_5["high"].max() > current_price + 2*atr) or (future_5["low"].min() < current_price - 2*atr):
                y_sweep.iloc[i] = 1
        
        # Align with X
        valid_idx = y_sweep.index.isin(X.index)
        y_sweep = y_sweep[valid_idx]
        X_aligned = X.loc[y_sweep.index]
        
        if y_sweep.sum() < 10:
            print("⚠️  Too few sweep examples. Skipping this model.")
            return {}
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_aligned, y_sweep, test_size=test_size, shuffle=False
        )
        
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Sweep Probability: {y_sweep.mean():.1%}")
        print(f"Accuracy: {accuracy:.1%}")
        
        self.models["sweep"] = model
        
        return {"accuracy": accuracy}
    
    def train_reversal_model(
        self,
        df: pd.DataFrame,
        X: pd.DataFrame,
        extremos: pd.DataFrame,
        test_size: float = 0.2
    ) -> Dict:
        """Train Model 3: Will there be a reversal after next sweep?"""
        
        print("\n" + "="*80)
        print("🎯 MODEL 3: REVERSAL AFTER SWEEP")
        print("="*80)
        
        # Create target: 1 if price reverses after reaching extreme
        y_reversal = pd.Series(0, index=df.index)
        
        if not extremos.empty:
            for i in range(len(df) - 5):
                future_5 = df.iloc[i:i+5]
                current_price = df["close"].iloc[i]
                
                # Check if touched extreme and then reversed
                extremo_prices = extremos[(extremos.index >= df.index[i]) & 
                                         (extremos.index <= df.index[min(i+5, len(df)-1)])]["price"].values
                
                if len(extremo_prices) > 0:
                    extreme = extremo_prices[0]
                    if extreme > current_price:  # Touched top
                        # Reversal if came back down
                        if future_5["close"].iloc[-1] < extreme * 0.99:
                            y_reversal.iloc[i] = 1
                    else:  # Touched bottom
                        # Reversal if came back up
                        if future_5["close"].iloc[-1] > extreme * 1.01:
                            y_reversal.iloc[i] = 1
        
        valid_idx = y_reversal.index.isin(X.index)
        y_reversal = y_reversal[valid_idx]
        X_aligned = X.loc[y_reversal.index]
        
        if y_reversal.sum() < 5:
            print("⚠️  Too few reversal examples. Skipping this model.")
            return {}
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_aligned, y_reversal, test_size=test_size, shuffle=False
        )
        
        model = xgb.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Reversal Probability: {y_reversal.mean():.1%}")
        print(f"Accuracy: {accuracy:.1%}")
        
        self.models["reversal"] = model
        return {"accuracy": accuracy}
    
    def train_expected_move_model(
        self,
        df: pd.DataFrame,
        X: pd.DataFrame,
        test_size: float = 0.2
    ) -> Dict:
        """Train Model 4: Predict expected move (range) for next day."""
        
        print("\n" + "="*80)
        print("🎯 MODEL 4: EXPECTED MOVE (REGRESSION)")
        print("="*80)
        
        # Target: Next day range in points
        y_range = (df["high"] - df["low"]).shift(-1)
        y_range = y_range[X.index]
        
        valid_idx = y_range.notna()
        X_train_set = X[valid_idx]
        y_train_set = y_range[valid_idx]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_train_set, y_train_set, test_size=test_size, shuffle=False
        )
        
        model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"Mean Absolute Error: {mae:.4f} points")
        print(f"R² Score: {r2:.1%}")
        print(f"Average Expected Move: {y_test.mean():.4f} points")
        
        self.models["expected_move"] = model
        return {"mae": mae, "r2": r2}
    
    def train_strike_selection_model(
        self,
        df: pd.DataFrame,
        X: pd.DataFrame,
        max_spread: float = 500,
        test_size: float = 0.2
    ) -> Dict:
        """
        Train Model 5: Predict if strikes within max_spread will expire OTM.
        
        This helps determine WHICH STRIKES to sell, not just IF to sell.
        """
        
        print("\n" + "="*80)
        print("🎯 MODEL 5: STRIKE SELECTION (OTM PROBABILITY)")
        print("="*80)
        
        # For each candle, check: if we sold put at -250 pts, would it expire OTM?
        # Target: 1 if closing price stayed above strike, 0 if not
        
        y_otm = pd.Series(0, index=df.index)
        
        for i in range(len(df) - 1):
            current_price = df["close"].iloc[i]
            next_price = df["close"].iloc[i + 1]
            
            # Check multiple strikes
            for strike_offset in [100, 200, 300, 400, 500]:
                put_strike = current_price - strike_offset
                
                # PUT expires OTM if price closes above strike
                if next_price > put_strike:
                    y_otm.iloc[i] = 1
                    break
        
        valid_idx = y_otm.index.isin(X.index)
        y_otm = y_otm[valid_idx]
        X_aligned = X.loc[y_otm.index]
        
        if len(y_otm) < 20:
            print("⚠️  Insufficient data for strike selection model.")
            return {}
        
        X_train, X_test, y_train, y_test = train_test_split(
            X_aligned, y_otm, test_size=test_size, shuffle=False
        )
        
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"OTM Probability: {y_otm.mean():.1%}")
        print(f"Accuracy: {accuracy:.1%}")
        
        self.models["strike_selection"] = model
        return {"accuracy": accuracy}
    
    def save_models(self) -> Path:
        """Save all trained models to disk."""
        model_file = self.output_dir / "smc_xgboost_models.pkl"
        
        with open(model_file, "wb") as f:
            pickle.dump({
                "models": self.models,
                "feature_names": self.feature_names
            }, f)
        
        print(f"\n✅ Models saved to: {model_file}")
        return model_file
    
    def train_all(
        self,
        df: pd.DataFrame,
        smc_features: pd.DataFrame,
        extremos: pd.DataFrame = None
    ):
        """Train all 5 models."""
        
        print("\n" + "#"*80)
        print("# MULTI-MODEL XGBOOST TRAINER - SMC FEATURES")
        print("#"*80)
        
        # Prepare data
        X, y_direction = self.prepare_data(df, smc_features)
        
        # Model 1: Direction
        self.train_direction_model(X, y_direction)
        
        # Model 2: Sweep
        self.train_sweep_model(df, X)
        
        # Model 3: Reversal
        if extremos is not None and not extremos.empty:
            self.train_reversal_model(df, X, extremos)
        
        # Model 4: Expected Move
        self.train_expected_move_model(df, X)
        
        # Model 5: Strike Selection
        self.train_strike_selection_model(df, X)
        
        # Save models
        self.save_models()
        
        print("\n" + "#"*80)
        print("# ALL MODELS TRAINED SUCCESSFULLY")
        print("#"*80)


if __name__ == "__main__":
    if not XGBOOST_AVAILABLE:
        print("ERROR: XGBoost not available")
        exit(1)
    
    print("SMC XGBoost Trainer Module Loaded Successfully")
