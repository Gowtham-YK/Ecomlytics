"""
Ecomlytics Data Ingestion and CSV Import Module.
Provides robust parsing, normalization, validation, idempotency,
and job tracking for orders, products, and customers.
"""

import csv
import io
import sqlite3
import uuid
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple


def _normalize_header(header: str) -> str:
    """Normalize column headers to lower_snake_case without spaces or symbols."""
    return header.strip().lower().replace(" ", "_").replace("-", "_")


def _parse_float(val: Any, default: float = 0.0) -> float:
    try:
        if val is None or str(val).strip() == "":
            return default
        return float(str(val).replace("$", "").replace("₹", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return default


def _parse_int(val: Any, default: int = 0) -> int:
    try:
        if val is None or str(val).strip() == "":
            return default
        return int(float(str(val).replace(",", "").strip()))
    except (ValueError, TypeError):
        return default


def _parse_date(val: Any) -> Optional[str]:
    if not val or not str(val).strip():
        return None
    s = str(val).strip()
    # Try ISO YYYY-MM-DD
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s.split(" ")[0].split("T")[0], fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return date.fromisoformat(s).isoformat()
    except Exception:
        return None


def import_csv_dataset(
    conn: sqlite3.Connection,
    workspace_id: str,
    dataset_type: str,
    csv_content: str,
    filename: str = "dataset.csv"
) -> Dict[str, Any]:
    """
    Parses and imports a CSV dataset into the specified workspace with idempotency.
    Returns summary dict with total_rows, imported_rows, skipped_rows, rejected_rows, and job_id.
    """
    valid_types = {"orders", "products", "customers"}
    clean_type = dataset_type.strip().lower()
    if clean_type not in valid_types:
        raise ValueError(f"Invalid dataset type '{dataset_type}'. Must be one of {valid_types}.")

    f = io.StringIO(csv_content.strip())
    reader = csv.reader(f)
    try:
        raw_headers = next(reader)
    except StopIteration:
        raise ValueError("The uploaded CSV file is empty.")

    normalized_headers = [_normalize_header(h) for h in raw_headers]
    header_map = {normalized_headers[i]: i for i in range(len(normalized_headers))}

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    total = 0
    imported = 0
    skipped = 0
    rejected = 0
    errors = []

    if clean_type == "orders":
        total, imported, skipped, rejected, errors = _process_orders(
            conn, workspace_id, reader, header_map
        )
    elif clean_type == "products":
        total, imported, skipped, rejected, errors = _process_products(
            conn, workspace_id, reader, header_map
        )
    elif clean_type == "customers":
        total, imported, skipped, rejected, errors = _process_customers(
            conn, workspace_id, reader, header_map
        )

    job_status = "completed" if rejected == 0 else ("completed_with_warnings" if imported > 0 else "failed")
    error_summary = "; ".join(errors[:5]) if errors else None

    # Record in import_jobs
    conn.execute(
        """
        INSERT INTO import_jobs (
            id, workspace_id, dataset_type, filename, status,
            total_rows, imported_rows, skipped_rows, rejected_rows, error_summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (job_id, workspace_id, clean_type, filename, job_status, total, imported, skipped, rejected, error_summary)
    )

    # Update or create data_sources record
    source_id = f"ds_{clean_type}_{workspace_id}"
    conn.execute(
        """
        INSERT INTO data_sources (id, workspace_id, source_type, name, status, last_synced, metadata_json)
        VALUES (?, ?, ?, ?, 'connected', CURRENT_TIMESTAMP, ?)
        ON CONFLICT(id) DO UPDATE SET
            status = 'connected',
            last_synced = CURRENT_TIMESTAMP,
            metadata_json = excluded.metadata_json
        """,
        (source_id, workspace_id, clean_type, f"{clean_type.title()} CSV", f'{{"total_rows": {total}, "imported": {imported}}}')
    )

    return {
        "job_id": job_id,
        "dataset_type": clean_type,
        "status": job_status,
        "total_rows": total,
        "imported_rows": imported,
        "skipped_rows": skipped,
        "rejected_rows": rejected,
        "errors": errors[:5]
    }


def _process_orders(
    conn: sqlite3.Connection,
    workspace_id: str,
    reader: Any,
    header_map: Dict[str, int]
) -> Tuple[int, int, int, int, List[str]]:
    total = imported = skipped = rejected = 0
    errors = []

    # Map candidate header names
    def get_val(row, *aliases):
        for alias in aliases:
            if alias in header_map and header_map[alias] < len(row):
                return row[header_map[alias]].strip()
        return None

    # Pre-fetch existing external IDs to handle idempotency cleanly
    existing_rows = conn.execute(
        "SELECT external_id FROM orders WHERE workspace_id = ?", (workspace_id,)
    ).fetchall()
    existing_ids = {r["external_id"] for r in existing_rows if r["external_id"]}

    for row_num, row in enumerate(reader, start=2):
        if not row or all(c.strip() == "" for c in row):
            continue
        total += 1

        ext_id = get_val(row, "order_id", "id", "order_number") or f"ord_row_{row_num}_{uuid.uuid4().hex[:6]}"
        if ext_id in existing_ids:
            skipped += 1
            continue

        raw_date = get_val(row, "order_date", "date", "created_at")
        parsed_date = _parse_date(raw_date)
        if not parsed_date:
            rejected += 1
            errors.append(f"Row {row_num}: Invalid or missing date '{raw_date}'")
            continue

        revenue = _parse_float(get_val(row, "revenue", "total", "amount", "order_total"), 0.0)
        quantity = _parse_int(get_val(row, "quantity", "qty", "items_count"), 1)
        status = (get_val(row, "status", "order_status") or "completed").strip().lower()
        cust_id = get_val(row, "customer_id", "cust_id", "customer")
        prod_id = get_val(row, "product_id", "prod_id", "product", "sku")

        order_pk = f"ord_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO orders (id, workspace_id, external_id, customer_id, product_id, order_date, quantity, revenue, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (order_pk, workspace_id, ext_id, cust_id, prod_id, parsed_date, quantity, revenue, status)
        )
        existing_ids.add(ext_id)
        imported += 1

    return total, imported, skipped, rejected, errors


def _process_products(
    conn: sqlite3.Connection,
    workspace_id: str,
    reader: Any,
    header_map: Dict[str, int]
) -> Tuple[int, int, int, int, List[str]]:
    total = imported = skipped = rejected = 0
    errors = []

    def get_val(row, *aliases):
        for alias in aliases:
            if alias in header_map and header_map[alias] < len(row):
                return row[header_map[alias]].strip()
        return None

    existing_rows = conn.execute(
        "SELECT external_id FROM products WHERE workspace_id = ?", (workspace_id,)
    ).fetchall()
    existing_ids = {r["external_id"] for r in existing_rows if r["external_id"]}

    for row_num, row in enumerate(reader, start=2):
        if not row or all(c.strip() == "" for c in row):
            continue
        total += 1

        name = get_val(row, "product_name", "name", "title")
        if not name:
            rejected += 1
            errors.append(f"Row {row_num}: Missing product name")
            continue

        ext_id = get_val(row, "product_id", "id", "sku") or f"prod_{uuid.uuid4().hex[:8]}"
        if ext_id in existing_ids:
            skipped += 1
            continue

        category = get_val(row, "category", "product_category") or "General"
        price = _parse_float(get_val(row, "price", "unit_price"), 0.0)
        cost = _parse_float(get_val(row, "cost", "unit_cost"), 0.0)

        prod_pk = f"prod_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO products (id, workspace_id, external_id, name, category, price, cost)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (prod_pk, workspace_id, ext_id, name, category, price, cost)
        )
        existing_ids.add(ext_id)
        imported += 1

    return total, imported, skipped, rejected, errors


def _process_customers(
    conn: sqlite3.Connection,
    workspace_id: str,
    reader: Any,
    header_map: Dict[str, int]
) -> Tuple[int, int, int, int, List[str]]:
    total = imported = skipped = rejected = 0
    errors = []

    def get_val(row, *aliases):
        for alias in aliases:
            if alias in header_map and header_map[alias] < len(row):
                return row[header_map[alias]].strip()
        return None

    existing_rows = conn.execute(
        "SELECT external_id FROM customers WHERE workspace_id = ?", (workspace_id,)
    ).fetchall()
    existing_ids = {r["external_id"] for r in existing_rows if r["external_id"]}

    for row_num, row in enumerate(reader, start=2):
        if not row or all(c.strip() == "" for c in row):
            continue
        total += 1

        ext_id = get_val(row, "customer_id", "id") or get_val(row, "email") or f"cust_{uuid.uuid4().hex[:8]}"
        if ext_id in existing_ids:
            skipped += 1
            continue

        name = get_val(row, "customer_name", "name", "full_name") or f"Customer {ext_id}"
        email = get_val(row, "email")
        city = get_val(row, "city", "location")

        cust_pk = f"cust_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO customers (id, workspace_id, external_id, name, email, city)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (cust_pk, workspace_id, ext_id, name, email, city)
        )
        existing_ids.add(ext_id)
        imported += 1

    return total, imported, skipped, rejected, errors


def get_import_jobs(conn: sqlite3.Connection, workspace_id: str) -> List[Dict[str, Any]]:
    """Retrieve history of import jobs for a workspace."""
    rows = conn.execute(
        """
        SELECT id, dataset_type, filename, status, total_rows, imported_rows, skipped_rows, rejected_rows, error_summary, created_at
        FROM import_jobs
        WHERE workspace_id = ?
        ORDER BY created_at DESC
        LIMIT 50
        """,
        (workspace_id,)
    ).fetchall()
    return [dict(r) for r in rows]
