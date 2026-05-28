"""
Decision Tree Post-Processor for Direction Classification
======================================================

After ensemble prediction of the close price, use a Decision Tree classifier
to improve directional accuracy (UP vs DOWN).

This layer uses signals from:
- XGBoost prediction
- RandomForest prediction  
- Ensemble prediction
- Confluence score
- Confidence percentage
- Advanced indicators (KAMA, ER, realized_vol, regime)

The decision tree learns patterns that correlate with correct direction prediction.
"""

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler


class DirectionPostProcessor:
    def __init__(self, max_depth=5, min_samples_split=10, random_state=42):
        """
        Initialize the direction post-processor.
        
        Args:
            max_depth: Max depth of decision tree
            min_samples_split: Minimum samples to split
            random_state: Random seed for reproducibility
        """
        self.dt = None
        self.scaler = StandardScaler()
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.random_state = random_state
        self.is_fitted = False
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for the decision tree."""
        features = pd.DataFrame(index=df.index)
        
        # Ensemble predictions (already normalized to 0-1 by model)
        features['xgb_pred'] = df['xgb_pred'] if 'xgb_pred' in df.columns else 0.5
        features['rf_pred'] = df['rf_pred'] if 'rf_pred' in df.columns else 0.5
        features['ensemble_pred'] = df['ensemble_pred'] if 'ensemble_pred' in df.columns else 0.5
        
        # Signal strength indicators
        features['confidence_pct'] = df['confidence_pct'] if 'confidence_pct' in df.columns else 50.0
        features['confluence_score'] = df['confluence_score'] if 'confluence_score' in df.columns else 3.0
        
        # Directional indicators
        features['rsi'] = df['rsi'] if 'rsi' in df.columns else 50.0
        features['momentum'] = df['momentum'] if 'momentum' in df.columns else 0.0
        features['macd'] = df['macd'] if 'macd' in df.columns else 0.0
        
        # Advanced indicators (if available)
        features['kama_trend'] = 0.0
        if 'kama' in df.columns and 'close' in df.columns:
            features['kama_trend'] = (df['close'] - df['kama']).fillna(0.0)
        
        features['er_efficiency'] = df['er'] if 'er' in df.columns else 0.5
        features['realized_vol'] = df['realized_vol'] if 'realized_vol' in df.columns else 0.0
        
        # Price action indicators
        features['price_above_sma20'] = df['price_above_sma20'].astype(float) if 'price_above_sma20' in df.columns else 0.0
        features['price_above_sma50'] = df['price_above_sma50'].astype(float) if 'price_above_sma50' in df.columns else 0.0
        
        # SMC signals
        features['smc_order_block'] = df['smc_order_block'].astype(float) if 'smc_order_block' in df.columns else 0.0
        features['smc_fvg'] = df['smc_fvg'].astype(float) if 'smc_fvg' in df.columns else 0.0
        
        return features.fillna(0.0)
    
    def create_target(self, df: pd.DataFrame) -> np.ndarray:
        """
        Create binary target: 1 if close went UP next day, 0 if DOWN.
        
        Args:
            df: DataFrame with price data including 'target_return' or compute from close
            
        Returns:
            Binary array (1 for UP, 0 for DOWN)
        """
        if 'target_return' in df.columns:
            # If target_return already exists
            target = (df['target_return'] > 0).astype(int).values
        elif 'close' in df.columns:
            # Compute from close prices
            next_close = df['close'].shift(-1)
            target = (next_close > df['close']).astype(int).values
            # Last value will be NaN, set to 0 (or drop)
            target[-1] = 0
        else:
            raise ValueError("Need either 'target_return' or 'close' column")
        
        return target
    
    def fit(self, df_train: pd.DataFrame):
        """
        Train the decision tree on training data.
        
        Args:
            df_train: DataFrame with features and price data
        """
        X = self.prepare_features(df_train)
        y = self.create_target(df_train)
        
        # Remove rows with NaN targets
        valid_idx = ~np.isnan(y)
        X = X.loc[valid_idx]
        y = y[valid_idx]
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train decision tree
        self.dt = DecisionTreeClassifier(
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            random_state=self.random_state,
            class_weight='balanced'  # Handle class imbalance
        )
        self.dt.fit(X_scaled, y)
        self.is_fitted = True
        
        # Log performance
        train_accuracy = self.dt.score(X_scaled, y)
        print(f"Decision Tree trained. Training accuracy: {train_accuracy:.2%}")
    
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predict direction using the trained decision tree.
        
        Args:
            df: DataFrame with features
            
        Returns:
            Array of predictions (1 for UP, 0 for DOWN)
        """
        if not self.is_fitted:
            raise ValueError("Decision tree not fitted yet")
        
        X = self.prepare_features(df)
        X_scaled = self.scaler.transform(X)
        predictions = self.dt.predict(X_scaled)
        
        return predictions
    
    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """
        Get probability predictions for both classes.
        
        Args:
            df: DataFrame with features
            
        Returns:
            Array of shape (n_samples, 2) with probabilities for [DOWN, UP]
        """
        if not self.is_fitted:
            raise ValueError("Decision tree not fitted yet")
        
        X = self.prepare_features(df)
        X_scaled = self.scaler.transform(X)
        proba = self.dt.predict_proba(X_scaled)
        
        return proba
    
    def apply_to_predictions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply decision tree post-processing to ensemble predictions.
        
        Modifies ensemble predictions based on decision tree output while
        preserving confidence levels.
        
        Args:
            df: DataFrame with ensemble predictions
            
        Returns:
            Modified DataFrame with adjusted predictions
        """
        df = df.copy()
        
        if not self.is_fitted:
            return df
        
        # Get tree predictions and probabilities
        tree_pred = self.predict(df)
        tree_proba = self.predict_proba(df)
        
        # tree_proba[:, 0] = P(DOWN), tree_proba[:, 1] = P(UP)
        tree_confidence = np.max(tree_proba, axis=1)
        
        # Blend ensemble prediction with tree prediction
        # If tree is confident, give it more weight
        df['dt_direction'] = tree_pred  # 0 = DOWN, 1 = UP
        df['dt_confidence'] = tree_confidence
        
        # New ensemble prediction: weighted average of price prediction and direction
        ensemble_dir = (df['ensemble_pred'] > 0.5).astype(float)
        
        # Blended direction (60% tree, 40% ensemble if tree is confident, else 50/50)
        blend_weight = np.minimum(tree_confidence, 0.6)
        df['final_direction'] = blend_weight * tree_pred + (1 - blend_weight) * ensemble_dir
        df['final_direction'] = df['final_direction'].round().astype(int)
        
        # Final confidence combines both signals
        ensemble_confidence = 1 - df['confidence_pct'].fillna(50) / 100
        df['final_confidence'] = (tree_confidence + ensemble_confidence) / 2
        df['final_confidence'] = df['final_confidence'].clip(0.5, 0.99)
        
        return df
