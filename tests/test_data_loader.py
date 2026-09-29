import pytest
from core.data_loader import DataCoDataLoader
from core.schema import OrderRecord, ShippingMode, CustomerTier

def test_data_loader_initialization():
    loader = DataCoDataLoader()
    df = loader.get_dataframe()
    assert df is not None
    assert len(df) >= 1000
    assert "Order Id" in df.columns
    assert "Product Name" in df.columns
    assert "Days for shipping (real)" in df.columns
    assert "Late_delivery_risk" in df.columns

def test_data_loader_sample_orders():
    loader = DataCoDataLoader()
    sample_size = 10
    orders = loader.sample_active_orders(n=sample_size, random_seed=123)
    
    assert len(orders) == sample_size
    for o in orders:
        assert isinstance(o, OrderRecord)
        assert o.order_id.startswith("ORD-")
        assert o.customer_id.startswith("CUST-")
        assert o.quantity >= 1
        assert o.total_value > 0.0
        assert o.customer_tier in CustomerTier
        assert o.shipping_mode in ShippingMode
