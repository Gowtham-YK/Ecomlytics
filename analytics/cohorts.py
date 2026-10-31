"""
Customer acquisition cohort and retention matrix engine.
Derives monthly customer retention tables strictly from verified order history.
"""

import sqlite3
from collections import defaultdict
from datetime import date
from typing import Dict, Any, List


def _month_diff(d1_str: str, d2_str: str) -> int:
    """Computes month difference: (year2 - year1) * 12 + (month2 - month1)."""
    y1, m1 = int(d1_str[:4]), int(d1_str[5:7])
    y2, m2 = int(d2_str[:4]), int(d2_str[5:7])
    return (y2 - y1) * 12 + (m2 - m1)


def compute_customer_cohorts(conn: sqlite3.Connection, workspace_id: str) -> Dict[str, Any]:
    """
    Computes monthly acquisition cohorts and retention rates.
    Identifies customer first purchase month (Period 0) and tracks
    repeat purchases in subsequent months (Period 1, 2, ...).
    """
    rows = conn.execute(
        """
        SELECT customer_id, order_date
        FROM orders
        WHERE workspace_id = ? AND LOWER(status) = 'completed' AND customer_id IS NOT NULL AND customer_id != ''
        ORDER BY order_date ASC
        """,
        (workspace_id,)
    ).fetchall()

    if not rows:
        return {
            "status": "insufficient_data",
            "message": "No completed customer orders available to build retention cohorts.",
            "cohorts": [],
            "max_periods": 0,
            "period_labels": []
        }

    # Map each customer to their first purchase date and all purchase months
    cust_first_date: Dict[str, str] = {}
    cust_purchase_months: Dict[str, set] = defaultdict(set)

    for r in rows:
        cid = r["customer_id"]
        odate = r["order_date"]
        month_str = odate[:7]  # YYYY-MM

        if cid not in cust_first_date:
            cust_first_date[cid] = odate
        cust_purchase_months[cid].add(month_str)

    # Group customers by cohort acquisition month
    cohort_members: Dict[str, List[str]] = defaultdict(list)
    for cid, first_date in cust_first_date.items():
        cohort_month = first_date[:7]
        cohort_members[cohort_month].append(cid)

    sorted_cohort_months = sorted(cohort_members.keys())
    if len(sorted_cohort_months) < 1:
        return {
            "status": "insufficient_data",
            "message": "Insufficient purchase history to establish multi-period retention cohorts.",
            "cohorts": [],
            "max_periods": 0,
            "period_labels": []
        }

    current_month_str = date.today().strftime("%Y-%m")
    cohort_results = []
    max_periods = 0

    for c_month in sorted_cohort_months:
        members = cohort_members[c_month]
        size = len(members)

        # Determine how many months have elapsed between c_month and current date
        elapsed_months = _month_diff(c_month + "-01", current_month_str + "-01")
        if elapsed_months < 0:
            elapsed_months = 0

        # Period 0 is always 100%
        periods = [{
            "period": 0,
            "retained_customers": size,
            "retention_rate": 100.0,
            "is_incomplete": False
        }]

        for k in range(1, elapsed_months + 1):
            # Target month for period k
            retained_count = 0
            for cid in members:
                # Check if customer made purchase in cohort_month + k
                for p_month in cust_purchase_months[cid]:
                    if _month_diff(c_month + "-01", p_month + "-01") == k:
                        retained_count += 1
                        break

            rate = round((retained_count / size) * 100, 1) if size > 0 else 0.0
            is_incomplete = (_month_diff(c_month + "-01", current_month_str + "-01") == k)
            periods.append({
                "period": k,
                "retained_customers": retained_count,
                "retention_rate": rate,
                "is_incomplete": is_incomplete
            })

        if len(periods) > max_periods:
            max_periods = len(periods)

        cohort_results.append({
            "cohort_month": c_month,
            "cohort_size": size,
            "periods": periods
        })

    period_labels = [f"Month {i}" if i > 0 else "Month 0" for i in range(max_periods)]

    return {
        "status": "available",
        "cohort_type": "Customer Acquisition Cohort",
        "cohorts": cohort_results,
        "max_periods": max_periods,
        "period_labels": period_labels
    }
