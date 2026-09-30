"""Machine Learning and Baseline Demand Forecasting Engine.

Trains LightGBM / Gradient Boosting Regressors against a Naive Seasonal Baseline.
Backtests models on out-of-time test windows, computing MAPE and WAPE metrics,
and generates point forecasts with uncertainty confidence intervals.
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Any, Optional

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

from sklearn.ensemble import GradientBoostingRegressor
from core.demand_data import build_demand_history, STORES, SKUS


def build_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create lag and rolling features for time-series forecasting."""
    df = df.sort_values(by=["store_id", "sku_id", "period"]).copy()

    # Create lag features
    df["lag_1"] = df.groupby(["store_id", "sku_id"])["demand"].shift(1)
    df["lag_2"] = df.groupby(["store_id", "sku_id"])["demand"].shift(2)
    df["rolling_mean_3"] = df.groupby(["store_id", "sku_id"])["demand"].shift(1).rolling(3, min_periods=1).mean()

    # Fill initial NaNs with backward fill or mean
    df["lag_1"] = df["lag_1"].bfill().fillna(20.0)
    df["lag_2"] = df["lag_2"].bfill().fillna(20.0)
    df["rolling_mean_3"] = df["rolling_mean_3"].bfill().fillna(20.0)

    # Encode categorical features
    df["store_code"] = df["store_id"].astype("category").cat.codes
    df["sku_code"] = df["sku_id"].astype("category").cat.codes

    return df


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute MAPE and WAPE accuracy metrics."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    # Prevent division by zero
    non_zero = y_true > 0
    mape = np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100.0

    sum_true = np.sum(y_true)
    wape = (np.sum(np.abs(y_true - y_pred)) / sum_true * 100.0) if sum_true > 0 else 0.0

    return {
        "MAPE": round(float(mape), 2),
        "WAPE": round(float(wape), 2)
    }


class DemandForecaster:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.ml_model = None
        self.metrics_report: Dict[str, Any] = {}
        self.is_trained = False

    def train_and_backtest(self, split_period: int = 18) -> Dict[str, Any]:
        """Train ML model, evaluate naive seasonal baseline, and save backtest metrics."""
        df_raw = build_demand_history(total_periods=24, seed=self.seed)
        df = build_lag_features(df_raw)

        feature_cols = ["store_code", "sku_code", "period", "seasonal_index", "lag_1", "lag_2", "rolling_mean_3"]

        train_df = df[df["period"] <= split_period]
        test_df = df[df["period"] > split_period].copy()

        X_train, y_train = train_df[feature_cols], train_df["demand"]
        X_test, y_test = test_df[feature_cols], test_df["demand"]

        # 1. Train LightGBM or Gradient Boosting
        if HAS_LIGHTGBM:
            model = lgb.LGBMRegressor(
                n_estimators=100,
                learning_rate=0.08,
                random_state=self.seed,
                verbose=-1
            )
        else:
            model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.08,
                random_state=self.seed
            )

        model.fit(X_train, y_train)
        self.ml_model = model
        self.is_trained = True

        y_pred_ml = model.predict(X_test)
        # Ensure non-negative predictions
        y_pred_ml = np.maximum(1.0, y_pred_ml)

        # 2. Naive Seasonal Baseline: uses lag_1 or seasonal rolling average
        y_pred_baseline = test_df["lag_1"].values

        # 3. Evaluate Backtest Metrics
        ml_metrics = calculate_metrics(y_test.values, y_pred_ml)
        baseline_metrics = calculate_metrics(y_test.values, y_pred_baseline)

        self.metrics_report = {
            "test_window_periods": [split_period + 1, 24],
            "sample_size": len(y_test),
            "ML_Model": {
                "algorithm": "LightGBM" if HAS_LIGHTGBM else "GradientBoosting",
                "MAPE_pct": ml_metrics["MAPE"],
                "WAPE_pct": ml_metrics["WAPE"]
            },
            "Naive_Seasonal_Baseline": {
                "algorithm": "Lag-1 Seasonal Persistence",
                "MAPE_pct": baseline_metrics["MAPE"],
                "WAPE_pct": baseline_metrics["WAPE"]
            },
            "wape_improvement_pct": round(baseline_metrics["WAPE"] - ml_metrics["WAPE"], 2)
        }

        # Save to disk
        out_dir = os.path.dirname(__file__)
        with open(os.path.join(out_dir, "backtest_metrics.json"), "w", encoding="utf-8") as f:
            json.dump(self.metrics_report, f, indent=2)

        return self.metrics_report

    def predict_horizon(
        self,
        horizon_length: int = 4,
        uncertainty_factor: float = 0.15
    ) -> Dict[Tuple[str, str, int], Dict[str, float]]:
        """Generate point forecast and uncertainty intervals for planning horizon.

        Returns:
          dict mapping (store_id, sku_id, period) -> {
             'point_forecast': float,
             'lower_bound_80': float,
             'upper_bound_80': float,
             'std_dev': float
          }
        """
        if not self.is_trained:
            self.train_and_backtest()

        forecasts: Dict[Tuple[str, str, int], Dict[str, float]] = {}
        # Simple recursive or direct forecast for horizon t=1..horizon_length
        df_hist = build_demand_history(total_periods=24, seed=self.seed)
        recent_demands = df_hist[df_hist["period"] == 24].set_index(["store_id", "sku_id"])["demand"].to_dict()

        for t in range(1, horizon_length + 1):
            future_period = 24 + t
            seasonal_factor = 1.0 + 0.25 * np.sin(2 * np.pi * (future_period % 12) / 12)

            for store_idx, store in enumerate(STORES):
                for sku_idx, sku in enumerate(SKUS):
                    last_val = recent_demands.get((store, sku), 30.0)

                    features = pd.DataFrame([{
                        "store_code": store_idx,
                        "sku_code": sku_idx,
                        "period": future_period,
                        "seasonal_index": seasonal_factor,
                        "lag_1": last_val,
                        "lag_2": last_val * 0.95,
                        "rolling_mean_3": last_val
                    }])

                    pred_val = float(self.ml_model.predict(features)[0])
                    pred_val = max(1.0, round(pred_val, 1))

                    std_err = pred_val * uncertainty_factor
                    forecasts[(store, sku, t)] = {
                        "point_forecast": pred_val,
                        "lower_bound_80": max(0.0, round(pred_val - 1.28 * std_err, 1)),
                        "upper_bound_80": round(pred_val + 1.28 * std_err, 1),
                        "std_dev": round(std_err, 2)
                    }

        return forecasts


forecaster = DemandForecaster()
