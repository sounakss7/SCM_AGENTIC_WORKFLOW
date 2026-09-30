"""Unit tests for ML Demand Forecaster and Naive Seasonal Baseline."""

from forecasting.forecaster import forecaster, calculate_metrics
import numpy as np


def test_calculate_metrics_exact():
    y_true = np.array([100.0, 200.0, 300.0])
    y_pred = np.array([110.0, 190.0, 300.0])

    m = calculate_metrics(y_true, y_pred)
    assert "MAPE" in m
    assert "WAPE" in m
    # Absolute errors: 10, 10, 0 => sum = 20. Total true = 600 => WAPE = 20/600 * 100 = 3.33%
    assert m["WAPE"] == 3.33


def test_forecaster_train_and_predict():
    report = forecaster.train_and_backtest()

    assert "ML_Model" in report
    assert "Naive_Seasonal_Baseline" in report
    assert report["ML_Model"]["WAPE_pct"] > 0.0
    assert report["Naive_Seasonal_Baseline"]["WAPE_pct"] > 0.0

    forecasts = forecaster.predict_horizon(horizon_length=4)
    assert len(forecasts) > 0
    sample = list(forecasts.values())[0]
    assert "point_forecast" in sample
    assert "lower_bound_80" in sample
    assert "upper_bound_80" in sample
    assert sample["upper_bound_80"] >= sample["lower_bound_80"]
