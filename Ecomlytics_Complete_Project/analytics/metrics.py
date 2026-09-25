
import csv
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"

def read_csv(name):
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def overview():
    products = read_csv("products.csv")
    customers = read_csv("customers.csv")
    orders = read_csv("orders.csv")
    revenue = sum(float(o["revenue"]) for o in orders if o["status"] != "Returned")
    units = sum(int(o["quantity"]) for o in orders if o["status"] != "Returned")
    return {
        "revenue": revenue,
        "orders": len(orders),
        "aov": revenue / len(orders) if orders else 0,
        "units": units,
        "customers": len(customers),
        "products": len(products),
        "repeat_rate": round(sum(1 for c in customers if int(c["orders"]) > 1) / len(customers) * 100, 1),
        "return_rate": round(sum(int(p["returns"]) for p in products) / max(units, 1) * 100, 1)
    }

def product_metrics():
    products = read_csv("products.csv")
    out = []
    for p in products:
        views = int(p["views"]); units = int(p["units_sold"])
        revenue = units * float(p["price"])
        margin = (float(p["price"]) - float(p["cost"])) * units
        out.append({
            **p,
            "views": views,
            "units_sold": units,
            "revenue": revenue,
            "margin": margin,
            "conversion": round(units / views * 100, 2),
            "return_rate": round(int(p["returns"]) / max(units, 1) * 100, 2)
        })
    return out

def customer_segments():
    customers = read_csv("customers.csv")
    counts = defaultdict(int); spend = defaultdict(float)
    for c in customers:
        counts[c["segment"]] += 1
        spend[c["segment"]] += float(c["total_spend"])
    return {"counts": dict(counts), "spend": dict(spend), "customers": customers}

def funnel():
    return {
        "stages": [
            {"name": "Product Views", "value": 100000},
            {"name": "Add to Cart", "value": 28400},
            {"name": "Checkout", "value": 15100},
            {"name": "Purchase", "value": 9200}
        ]
    }
