"""
Centralized workspace-scoped analytics service.
Queries persisted database records and computes standardized e-commerce metrics
with strict multi-tenant isolation and honest zero/empty data handling.
"""

import sqlite3
from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict


def _pct(val: float, total: float, decimals: int = 1) -> float:
    if total <= 0:
        return 0.0
    return round((val / total) * 100, decimals)


def _pct_change(current: float, previous: float) -> Optional[float]:
    if previous is None or previous <= 0:
        return None
    return round(((current - previous) / previous) * 100, 1)


def get_workspace_overview(conn: sqlite3.Connection, workspace_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Computes overview KPI metrics for the specified workspace.
    Returns honest no_data state if workspace has no orders.
    """
    # 1. Orders and Revenue
    orders_row = conn.execute(
        """
        SELECT 
            COUNT(CASE WHEN LOWER(status) = 'completed' THEN 1 END) as completed_orders,
            COALESCE(SUM(CASE WHEN LOWER(status) = 'completed' THEN revenue ELSE 0 END), 0.0) as total_revenue,
            COALESCE(SUM(CASE WHEN LOWER(status) = 'completed' THEN quantity ELSE 0 END), 0) as total_units,
            COUNT(CASE WHEN LOWER(status) = 'returned' THEN 1 END) as returned_orders,
            MAX(order_date) as max_date
        FROM orders
        WHERE workspace_id = ?
        """,
        (workspace_id,)
    ).fetchone()

    completed_orders = orders_row["completed_orders"] or 0
    revenue = round(float(orders_row["total_revenue"] or 0.0), 2)
    units = int(orders_row["total_units"] or 0)
    returned_orders = int(orders_row["returned_orders"] or 0)
    max_date_str = orders_row["max_date"]

    aov = round(revenue / completed_orders, 2) if completed_orders > 0 else 0.0
    total_delivered = completed_orders + returned_orders
    return_rate = _pct(returned_orders, total_delivered, 1)

    # 2. Customers
    cust_count_row = conn.execute(
        "SELECT COUNT(*) as cnt FROM customers WHERE workspace_id = ?",
        (workspace_id,)
    ).fetchone()
    customer_count = cust_count_row["cnt"] if cust_count_row else 0

    # Repeat Customers (based on orders)
    repeat_rows = conn.execute(
        """
        SELECT customer_id, COUNT(*) as ord_cnt
        FROM orders
        WHERE workspace_id = ? AND LOWER(status) = 'completed' AND customer_id IS NOT NULL AND customer_id != ''
        GROUP BY customer_id
        """,
        (workspace_id,)
    ).fetchall()

    purchasing_customers = len(repeat_rows)
    repeat_customers = sum(1 for r in repeat_rows if r["ord_cnt"] > 1)
    # If customer table is empty, use purchasing_customers as base
    base_cust = customer_count if customer_count > 0 else purchasing_customers
    repeat_rate = _pct(repeat_customers, base_cust, 1)

    # 3. Products & Profit
    prod_count_row = conn.execute(
        "SELECT COUNT(*) as cnt FROM products WHERE workspace_id = ?",
        (workspace_id,)
    ).fetchone()
    product_count = prod_count_row["cnt"] if prod_count_row else 0

    profit_row = conn.execute(
        """
        SELECT COALESCE(SUM((p.price - p.cost) * o.quantity), 0.0) as profit
        FROM orders o
        JOIN products p ON o.product_id = p.external_id AND o.workspace_id = p.workspace_id
        WHERE o.workspace_id = ? AND LOWER(o.status) = 'completed'
        """,
        (workspace_id,)
    ).fetchone()
    profit = round(float(profit_row["profit"] or 0.0), 2)

    # 4. Period Comparison
    comparison = _calculate_period_comparison(conn, workspace_id, max_date_str, days)

    has_data = (completed_orders > 0 or product_count > 0 or customer_count > 0)
    data_status = "available" if has_data else "no_data"

    return {
        "status": data_status,
        "revenue": revenue,
        "orders": completed_orders,
        "aov": aov,
        "units": units,
        "customers": customer_count if customer_count > 0 else purchasing_customers,
        "products": product_count,
        "repeat_rate": repeat_rate,
        "return_rate": return_rate,
        "profit": profit,
        "returned_orders": returned_orders,
        "currency": "INR",
        "comparison": comparison
    }


def _calculate_period_comparison(
    conn: sqlite3.Connection,
    workspace_id: str,
    max_date_str: Optional[str],
    days: int = 30
) -> Dict[str, Any]:
    """Calculates period-over-period change for recent window vs previous window."""
    if not max_date_str:
        return {
            "period_days": days,
            "status": "insufficient_data",
            "note": "No orders available for period comparison.",
            "metrics": {
                "revenue": {"value": 0.0, "change_pct": None},
                "orders": {"value": 0, "change_pct": None},
                "aov": {"value": 0.0, "change_pct": None},
                "repeat_rate": {"value": 0.0, "change_pct": None}
            }
        }

    try:
        end_date = date.fromisoformat(max_date_str)
    except Exception:
        end_date = date.today()

    cur_start = end_date - timedelta(days=days - 1)
    prev_end = cur_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)

    cur_stats = _query_window_stats(conn, workspace_id, cur_start.isoformat(), end_date.isoformat())
    prev_stats = _query_window_stats(conn, workspace_id, prev_start.isoformat(), prev_end.isoformat())

    return {
        "period_days": days,
        "current_window": f"{cur_start.isoformat()} to {end_date.isoformat()}",
        "previous_window": f"{prev_start.isoformat()} to {prev_end.isoformat()}",
        "status": "available" if prev_stats["orders"] > 0 else "insufficient_data",
        "metrics": {
            "revenue": {
                "value": cur_stats["revenue"],
                "change_pct": _pct_change(cur_stats["revenue"], prev_stats["revenue"])
            },
            "orders": {
                "value": cur_stats["orders"],
                "change_pct": _pct_change(cur_stats["orders"], prev_stats["orders"])
            },
            "aov": {
                "value": cur_stats["aov"],
                "change_pct": _pct_change(cur_stats["aov"], prev_stats["aov"])
            },
            "repeat_rate": {
                "value": cur_stats["repeat_rate"],
                "change_pct": _pct_change(cur_stats["repeat_rate"], prev_stats["repeat_rate"])
            }
        }
    }


def _query_window_stats(conn: sqlite3.Connection, workspace_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
    row = conn.execute(
        """
        SELECT 
            COUNT(CASE WHEN LOWER(status) = 'completed' THEN 1 END) as orders,
            COALESCE(SUM(CASE WHEN LOWER(status) = 'completed' THEN revenue ELSE 0 END), 0.0) as revenue
        FROM orders
        WHERE workspace_id = ? AND order_date >= ? AND order_date <= ?
        """,
        (workspace_id, start_date, end_date)
    ).fetchone()

    orders = row["orders"] or 0
    revenue = round(float(row["revenue"] or 0.0), 2)
    aov = round(revenue / orders, 2) if orders > 0 else 0.0

    cust_rows = conn.execute(
        """
        SELECT customer_id, COUNT(*) as ord_cnt
        FROM orders
        WHERE workspace_id = ? AND order_date >= ? AND order_date <= ?
          AND LOWER(status) = 'completed' AND customer_id IS NOT NULL
        GROUP BY customer_id
        """,
        (workspace_id, start_date, end_date)
    ).fetchall()
    total_cust = len(cust_rows)
    repeat_cust = sum(1 for r in cust_rows if r["ord_cnt"] > 1)
    repeat_rate = _pct(repeat_cust, total_cust, 1)

    return {
        "orders": orders,
        "revenue": revenue,
        "aov": aov,
        "repeat_rate": repeat_rate
    }


def get_workspace_sales_trend(conn: sqlite3.Connection, workspace_id: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Returns daily sales trend for the workspace."""
    rows = conn.execute(
        """
        SELECT 
            order_date,
            COUNT(*) as orders,
            ROUND(SUM(revenue), 2) as revenue,
            SUM(quantity) as units
        FROM orders
        WHERE workspace_id = ? AND LOWER(status) = 'completed'
        GROUP BY order_date
        ORDER BY order_date DESC
        LIMIT ?
        """,
        (workspace_id, limit)
    ).fetchall()
    # Return chronologically ascending
    return [dict(r) for r in reversed(rows)]


def get_workspace_products(conn: sqlite3.Connection, workspace_id: str) -> List[Dict[str, Any]]:
    """Returns products with aggregated sales metrics for the workspace."""
    rows = conn.execute(
        """
        SELECT 
            p.id,
            p.external_id,
            p.name,
            p.category,
            p.price,
            p.cost,
            COALESCE(SUM(CASE WHEN LOWER(o.status) = 'completed' THEN o.quantity ELSE 0 END), 0) as units_sold,
            ROUND(COALESCE(SUM(CASE WHEN LOWER(o.status) = 'completed' THEN o.revenue ELSE 0 END), 0.0), 2) as revenue,
            COUNT(CASE WHEN LOWER(o.status) = 'returned' THEN 1 END) as returns
        FROM products p
        LEFT JOIN orders o ON p.external_id = o.product_id AND p.workspace_id = o.workspace_id
        WHERE p.workspace_id = ?
        GROUP BY p.id
        ORDER BY revenue DESC
        """,
        (workspace_id,)
    ).fetchall()

    result = []
    for r in rows:
        d = dict(r)
        units = d["units_sold"]
        returns = d["returns"]
        d["return_rate"] = _pct(returns, units + returns, 1)
        # Margin
        price = d["price"] or 0.0
        cost = d["cost"] or 0.0
        d["margin"] = round(((price - cost) / price) * 100, 1) if price > 0 else 0.0
        result.append(d)
    return result


def get_workspace_customer_segments(conn: sqlite3.Connection, workspace_id: str) -> Dict[str, Any]:
    """Calculates customer RFM segments for the workspace."""
    rows = conn.execute(
        """
        SELECT 
            c.id,
            c.external_id,
            c.name,
            c.email,
            c.city,
            COUNT(o.id) as orders,
            ROUND(COALESCE(SUM(o.revenue), 0.0), 2) as total_spend,
            MAX(o.order_date) as last_order_date
        FROM customers c
        LEFT JOIN orders o ON c.external_id = o.customer_id AND c.workspace_id = o.workspace_id AND LOWER(o.status) = 'completed'
        WHERE c.workspace_id = ?
        GROUP BY c.id
        """,
        (workspace_id,)
    ).fetchall()

    segments = {
        "Champions": [],
        "Loyal Customers": [],
        "Potential Loyalists": [],
        "At Risk": [],
        "One-Time Buyers": [],
        "Prospects": []
    }

    today = date.today()

    for r in rows:
        d = dict(r)
        ord_cnt = d["orders"] or 0
        spend = d["total_spend"] or 0.0
        last_date_str = d["last_order_date"]

        days_ago = None
        if last_date_str:
            try:
                days_ago = (today - date.fromisoformat(last_date_str)).days
            except Exception:
                days_ago = None

        if ord_cnt == 0:
            segments["Prospects"].append(d)
        elif ord_cnt >= 3 and spend >= 2000 and (days_ago is not None and days_ago <= 45):
            segments["Champions"].append(d)
        elif ord_cnt >= 2 and (days_ago is not None and days_ago <= 60):
            segments["Loyal Customers"].append(d)
        elif days_ago is not None and days_ago > 60:
            segments["At Risk"].append(d)
        elif ord_cnt >= 2:
            segments["Potential Loyalists"].append(d)
        else:
            segments["One-Time Buyers"].append(d)

    summary = {name: len(custs) for name, custs in segments.items()}
    return {
        "summary": summary,
        "segments": segments
    }
