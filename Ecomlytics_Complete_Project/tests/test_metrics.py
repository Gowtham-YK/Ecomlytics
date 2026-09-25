from analytics.metrics import overview, product_metrics
def test_overview():
    assert overview()["orders"] == 16
def test_products():
    assert len(product_metrics()) == 8
