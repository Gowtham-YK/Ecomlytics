import csv
from pathlib import Path
from datetime import date, timedelta
import random

random.seed(123)

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

# 1. PRODUCTS
products_data = [
    {"product_id": "P001", "product_name": "Premium Hoodie", "category": "Fashion", "price": 799, "cost": 380, "views": 260, "add_to_cart": 42, "checkout": 24, "units_sold": 14, "returns": 1, "rating": 4.2},
    {"product_id": "P002", "product_name": "Running Shoes", "category": "Footwear", "price": 899, "cost": 450, "views": 310, "add_to_cart": 58, "checkout": 36, "units_sold": 22, "returns": 1, "rating": 4.5},
    {"product_id": "P003", "product_name": "Wireless Earbuds", "category": "Electronics", "price": 699, "cost": 320, "views": 240, "add_to_cart": 38, "checkout": 21, "units_sold": 12, "returns": 0, "rating": 4.0},
    {"product_id": "P004", "product_name": "Smart Watch", "category": "Electronics", "price": 999, "cost": 500, "views": 280, "add_to_cart": 46, "checkout": 28, "units_sold": 16, "returns": 1, "rating": 4.3},
    {"product_id": "P005", "product_name": "Cotton T-Shirt", "category": "Fashion", "price": 399, "cost": 150, "views": 340, "add_to_cart": 64, "checkout": 40, "units_sold": 26, "returns": 1, "rating": 4.4},
    {"product_id": "P006", "product_name": "Denim Jacket", "category": "Fashion", "price": 899, "cost": 420, "views": 180, "add_to_cart": 28, "checkout": 16, "units_sold": 9, "returns": 0, "rating": 3.9},
    {"product_id": "P007", "product_name": "Laptop Backpack", "category": "Accessories", "price": 699, "cost": 310, "views": 290, "add_to_cart": 52, "checkout": 32, "units_sold": 18, "returns": 1, "rating": 4.6},
    {"product_id": "P008", "product_name": "Bluetooth Speaker", "category": "Electronics", "price": 599, "cost": 280, "views": 210, "add_to_cart": 34, "checkout": 19, "units_sold": 11, "returns": 1, "rating": 3.8},
    {"product_id": "P009", "product_name": "Sunglasses", "category": "Accessories", "price": 399, "cost": 160, "views": 190, "add_to_cart": 30, "checkout": 17, "units_sold": 10, "returns": 0, "rating": 4.1},
    {"product_id": "P010", "product_name": "Sports Track Pants", "category": "Fashion", "price": 499, "cost": 220, "views": 250, "add_to_cart": 44, "checkout": 26, "units_sold": 15, "returns": 1, "rating": 4.3},
    {"product_id": "P011", "product_name": "Face Serum", "category": "Beauty", "price": 499, "cost": 190, "views": 220, "add_to_cart": 36, "checkout": 22, "units_sold": 13, "returns": 1, "rating": 4.2},
    {"product_id": "P012", "product_name": "Moisturizer", "category": "Beauty", "price": 349, "cost": 120, "views": 270, "add_to_cart": 48, "checkout": 30, "units_sold": 19, "returns": 1, "rating": 4.5},
    {"product_id": "P013", "product_name": "Coffee Maker", "category": "Home", "price": 899, "cost": 450, "views": 160, "add_to_cart": 26, "checkout": 14, "units_sold": 8, "returns": 0, "rating": 4.1},
    {"product_id": "P014", "product_name": "Air Fryer", "category": "Home", "price": 999, "cost": 520, "views": 230, "add_to_cart": 39, "checkout": 22, "units_sold": 12, "returns": 1, "rating": 4.4},
    {"product_id": "P015", "product_name": "Yoga Mat", "category": "Fitness", "price": 399, "cost": 150, "views": 200, "add_to_cart": 32, "checkout": 18, "units_sold": 10, "returns": 0, "rating": 4.0}
]

with open(DATA / "products.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["product_id","product_name","category","price","cost","views","add_to_cart","checkout","units_sold","returns","rating"])
    writer.writeheader()
    writer.writerows(products_data)

# 2. CUSTOMERS (40 customers)
first_names = ["Aarav", "Priya", "Rohan", "Ananya", "Vikram", "Neha", "Aditya", "Sneha", "Kabir", "Pooja", "Arjun", "Tanvi", "Devansh", "Ishita", "Karan"]
last_names = ["Sharma", "Patel", "Kumar", "Singh", "Reddy", "Nair", "Gupta", "Verma", "Joshi", "Mehta"]
cities = ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Pune", "Kolkata"]

customers_data = []
for i in range(1, 41):
    cid = f"C{i:04d}"
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    city = random.choice(cities)
    orders_cnt = random.randint(1, 4)
    spend = orders_cnt * random.randint(399, 899)
    last_days = random.randint(2, 60)
    last_date = date.today() - timedelta(days=last_days)
    first_date = last_date - timedelta(days=random.randint(15, 120))
    customers_data.append({
        "customer_id": cid,
        "customer_name": name,
        "city": city,
        "orders": orders_cnt,
        "total_spend": spend,
        "last_order_days": last_days,
        "first_order_date": first_date.isoformat(),
        "last_order_date": last_date.isoformat()
    })

with open(DATA / "customers.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["customer_id","customer_name","city","orders","total_spend","last_order_days","first_order_date","last_order_date"])
    writer.writeheader()
    writer.writerows(customers_data)

# 3. ORDERS (65 orders total)
orders_data = []
start_date = date.today() - timedelta(days=60)

for i in range(1, 66):
    oid = f"O{i:06d}"
    c = random.choice(customers_data)
    p = random.choice(products_data)
    qty = 1 if random.random() > 0.15 else 2
    price = p["price"]
    discount = 0 if random.random() > 0.2 else random.choice([20, 50])
    rev = max(0, price * qty - discount)
    odate = start_date + timedelta(days=random.randint(0, 60))
    
    roll = random.random()
    status = "Completed" if roll < 0.90 else ("Returned" if roll < 0.96 else "Cancelled")
    
    orders_data.append({
        "order_id": oid,
        "customer_id": c["customer_id"],
        "product_id": p["product_id"],
        "order_date": odate.isoformat(),
        "quantity": qty,
        "price": price,
        "discount": discount,
        "revenue": float(rev),
        "status": status
    })

with open(DATA / "orders.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["order_id","customer_id","product_id","order_date","quantity","price","discount","revenue","status"])
    writer.writeheader()
    writer.writerows(orders_data)

print("Generic demo datasets generated successfully!")
