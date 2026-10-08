import csv
import random
from pathlib import Path
from datetime import date, timedelta

# ============================================================
# CONFIGURATION
# ============================================================

random.seed(42)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# BASIC DATA
# ============================================================

FIRST_NAMES = [
    "Aarav", "Aditya", "Akash", "Arjun", "Aryan",
    "Aditi", "Ananya", "Anika", "Diya", "Isha",
    "Kavya", "Meera", "Neha", "Pooja", "Riya",
    "Sahana", "Shreya", "Sneha", "Tanvi", "Varsha"
]

LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Singh", "Reddy",
    "Nair", "Gupta", "Verma", "Joshi", "Mehta",
    "Rao", "Iyer", "Shah", "Das", "Bhat"
]

CITIES = [
    "Bengaluru",
    "Mumbai",
    "Delhi",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Kolkata",
    "Ahmedabad",
    "Jaipur",
    "Kochi"
]

PRODUCTS = [
    {
        "product_id": "P001",
        "product_name": "Premium Hoodie",
        "category": "Fashion",
        "price": 899,
        "cost": 420,
        "rating": 3.8,
        "performance": "weak_conversion"
    },
    {
        "product_id": "P002",
        "product_name": "Running Shoes",
        "category": "Footwear",
        "price": 1299,
        "cost": 650,
        "rating": 4.4,
        "performance": "best"
    },
    {
        "product_id": "P003",
        "product_name": "Wireless Earbuds",
        "category": "Electronics",
        "price": 999,
        "cost": 480,
        "rating": 3.9,
        "performance": "normal"
    },
    {
        "product_id": "P004",
        "product_name": "Smart Watch",
        "category": "Electronics",
        "price": 1499,
        "cost": 750,
        "rating": 4.2,
        "performance": "best"
    },
    {
        "product_id": "P005",
        "product_name": "Cotton T-Shirt",
        "category": "Fashion",
        "price": 399,
        "cost": 160,
        "rating": 4.1,
        "performance": "best"
    },
    {
        "product_id": "P006",
        "product_name": "Denim Jacket",
        "category": "Fashion",
        "price": 999,
        "cost": 480,
        "rating": 3.9,
        "performance": "normal"
    },
    {
        "product_id": "P007",
        "product_name": "Laptop Backpack",
        "category": "Accessories",
        "price": 799,
        "cost": 360,
        "rating": 4.5,
        "performance": "best"
    },
    {
        "product_id": "P008",
        "product_name": "Bluetooth Speaker",
        "category": "Electronics",
        "price": 899,
        "cost": 420,
        "rating": 3.7,
        "performance": "normal"
    },
    {
        "product_id": "P009",
        "product_name": "Sunglasses",
        "category": "Accessories",
        "price": 499,
        "cost": 200,
        "rating": 4.0,
        "performance": "normal"
    },
    {
        "product_id": "P010",
        "product_name": "Sports Track Pants",
        "category": "Fashion",
        "price": 699,
        "cost": 310,
        "rating": 4.3,
        "performance": "best"
    },
    {
        "product_id": "P011",
        "product_name": "Face Serum",
        "category": "Beauty",
        "price": 599,
        "cost": 240,
        "rating": 4.2,
        "performance": "normal"
    },
    {
        "product_id": "P012",
        "product_name": "Moisturizer",
        "category": "Beauty",
        "price": 399,
        "cost": 150,
        "rating": 4.4,
        "performance": "best"
    },
    {
        "product_id": "P013",
        "product_name": "Coffee Maker",
        "category": "Home",
        "price": 1299,
        "cost": 680,
        "rating": 4.1,
        "performance": "normal"
    },
    {
        "product_id": "P014",
        "product_name": "Air Fryer",
        "category": "Home",
        "price": 1499,
        "cost": 790,
        "rating": 4.5,
        "performance": "best"
    },
    {
        "product_id": "P015",
        "product_name": "Yoga Mat",
        "category": "Fitness",
        "price": 499,
        "cost": 190,
        "rating": 3.9,
        "performance": "normal"
    }
]


# ============================================================
# GENERATE PRODUCTS
# ============================================================

def generate_products():

    rows = []

    for product in PRODUCTS:

        performance = product["performance"]

        if performance == "weak_conversion":
            views = 1850
            add_to_cart = 160
            checkout = 95
            units_sold = 32
            returns = 4

        elif performance == "best":
            views = random.randint(1100, 1800)
            add_to_cart = int(views * random.uniform(0.16, 0.22))
            checkout = int(add_to_cart * random.uniform(0.55, 0.70))
            units_sold = int(checkout * random.uniform(0.60, 0.75))
            returns = int(units_sold * random.uniform(0.015, 0.035))

        else:
            views = random.randint(650, 1200)
            add_to_cart = int(views * random.uniform(0.10, 0.16))
            checkout = int(add_to_cart * random.uniform(0.45, 0.62))
            units_sold = int(checkout * random.uniform(0.50, 0.68))
            returns = int(units_sold * random.uniform(0.025, 0.055))

        rows.append({
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "category": product["category"],
            "price": product["price"],
            "cost": product["cost"],
            "views": views,
            "add_to_cart": add_to_cart,
            "checkout": checkout,
            "units_sold": units_sold,
            "returns": returns,
            "rating": product["rating"]
        })

    return rows


# ============================================================
# GENERATE CUSTOMERS
# ============================================================

def generate_customers(count=120):

    rows = []

    for i in range(1, count + 1):

        customer_id = f"C{i:04d}"

        name = (
            random.choice(FIRST_NAMES)
            + " "
            + random.choice(LAST_NAMES)
        )

        city = random.choice(CITIES)

        customer_type = random.random()

        if customer_type < 0.08:
            orders = random.randint(4, 7)
            total_spend = random.randint(2400, 4800)
            last_order_days = random.randint(1, 15)

        elif customer_type < 0.30:
            orders = random.randint(3, 5)
            total_spend = random.randint(1200, 2500)
            last_order_days = random.randint(1, 30)

        elif customer_type < 0.50:
            orders = random.randint(2, 3)
            total_spend = random.randint(600, 1400)
            last_order_days = random.randint(5, 45)

        elif customer_type < 0.78:
            orders = 1
            total_spend = random.randint(299, 899)
            last_order_days = random.randint(1, 30)

        else:
            orders = random.randint(2, 4)
            total_spend = random.randint(700, 1800)
            last_order_days = random.randint(61, 150)

        last_date = (
            date.today()
            - timedelta(days=last_order_days)
        )

        first_date = (
            last_date
            - timedelta(
                days=random.randint(
                    30,
                    200
                )
            )
        )

        rows.append({
            "customer_id": customer_id,
            "customer_name": name,
            "city": city,
            "orders": orders,
            "total_spend": total_spend,
            "last_order_days": last_order_days,
            "first_order_date": first_date.isoformat(),
            "last_order_date": last_date.isoformat()
        })

    return rows


# ============================================================
# GENERATE ORDERS
# ============================================================

def generate_orders(
    customers,
    products,
    count=200
):

    rows = []

    customer_weights = []

    for customer in customers:
        weight = max(1, int(customer["orders"]))
        customer_weights.append(weight)

    customer_pool = []

    for customer, weight in zip(customers, customer_weights):
        customer_pool.extend([customer] * weight)

    start_date = date.today() - timedelta(days=90)

    for i in range(1, count + 1):

        order_id = f"O{i:06d}"

        customer = random.choice(customer_pool)
        product = random.choice(products)

        quantity = random.randint(1, 2)
        price = float(product["price"])

        discount = random.choice([0, 0, 20, 50, 80])

        gross = price * quantity
        revenue = max(0, gross - discount)

        order_date = start_date + timedelta(days=random.randint(0, 90))

        status_roll = random.random()

        if status_roll < 0.92:
            status = "Completed"
        elif status_roll < 0.97:
            status = "Returned"
        else:
            status = "Cancelled"

        rows.append({
            "order_id": order_id,
            "customer_id": customer["customer_id"],
            "product_id": product["product_id"],
            "order_date": order_date.isoformat(),
            "quantity": quantity,
            "price": int(price),
            "discount": discount,
            "revenue": round(revenue, 2),
            "status": status
        })

    return rows


# ============================================================
# WRITE CSV
# ============================================================

def write_csv(filename, rows):

    if not rows:
        return

    filepath = DATA_DIR / filename

    with open(
        filepath,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys()
        )

        writer.writeheader()

        writer.writerows(rows)

    print(
        f"Created: {filepath}"
    )

    print(
        f"Rows: {len(rows)}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("ECOMLYTICS DATASET GENERATOR")
    print("=" * 60)

    print()

    # Products

    products = generate_products()

    write_csv(
        "products.csv",
        products
    )

    # Customers

    customers = generate_customers(
        count=120
    )

    write_csv(
        "customers.csv",
        customers
    )

    # Orders

    orders = generate_orders(
        customers,
        products,
        count=180
    )

    write_csv(
        "orders.csv",
        orders
    )

    print()

    print("=" * 60)
    print("DATASET GENERATION COMPLETE")
    print("=" * 60)

    print()

    print(
        f"Products : {len(products)}"
    )

    print(
        f"Customers: {len(customers)}"
    )

    print(
        f"Orders   : {len(orders)}"
    )

    print()

    print(
        f"Files saved in: {DATA_DIR}"
    )


if __name__ == "__main__":
    main()