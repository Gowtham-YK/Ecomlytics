# Ecomlytics — Central Metric Definitions Catalogue (Stage G)

**Document Reference:** Section 7 of Ecomlytics Master Implementation Specification  
**Application:** Ecomlytics Analytics Engine  
**Version:** 2.0.0  
**Date:** October 31, 2026  

---

## 1. Principles of Metric Governance

1. **Single Source of Truth:** A metric must have exactly one implementation in code and one documentation entry.
2. **Explicit Denominators:** Denominators must never default to zero without handling. If the denominator is zero, the calculation returns `null` or $0.0$, accompanied by an explicit status (`no_data` or `insufficient_data`), rather than fabricating an arbitrary number.
3. **Workspace Isolation:** Every aggregation query is strictly bounded by `workspace_id`.
4. **Order Status Rules:**
   - Completed revenue counts only orders where `status = 'completed'`.
   - Returned orders have `status = 'returned'`.
   - Cancelled orders have `status = 'cancelled'`.

---

## 2. Metric Specifications

### 2.1 Total Completed Revenue
- **Description:** Sum of revenue from all qualifying completed orders in the workspace.
- **Formula:** $\sum \text{revenue}$ for orders where `status = 'completed'`.
- **Source:** `orders` table (`workspace_id`, `status = 'completed'`).
- **Currency:** Explicitly tracked per workspace (default `INR` / `₹`).
- **No Data Behavior:** Returns $0.00$ with status `"no_data"`.

### 2.2 Order Count
- **Description:** Count of completed order records in the workspace.
- **Formula:** $\text{COUNT}(*)$ for orders where `status = 'completed'`.
- **Source:** `orders` table.
- **No Data Behavior:** Returns $0$.

### 2.3 Average Order Value (AOV)
- **Description:** Average monetary value generated per completed order.
- **Formula:** $\frac{\text{Completed Revenue}}{\text{Completed Order Count}}$
- **No Data Behavior:** When order count is 0, AOV returns $0.00$ or `null`. No fabricated baseline is assumed.

### 2.4 Units Sold
- **Description:** Total quantity of product units sold across completed orders.
- **Formula:** $\sum \text{quantity}$ for orders where `status = 'completed'`.
- **Source:** `orders` table.

### 2.5 Repeat Customer Rate
- **Description:** Percentage of purchasing customers who have completed more than one order.
- **Formula:** $\frac{\text{Count of customers with } > 1 \text{ completed orders}}{\text{Total distinct purchasing customers}} \times 100$
- **Denominator Rule:** If total customers with orders is 0, rate returns $0.0\%$.

### 2.6 Return Rate
- **Description:** Proportion of orders that were returned by customers.
- **Formula:** $\frac{\text{Count of returned orders}}{\text{Count of completed} + \text{returned orders}} \times 100$
- **Denominator Rule:** If completed + returned orders is 0, return rate returns $0.0\%$.

### 2.7 Period-over-Period Growth
- **Description:** Percentage difference between the current window (e.g. recent 30 days) and the immediately preceding window of identical duration.
- **Formula:** $\frac{\text{Current Period Value} - \text{Previous Period Value}}{\text{Previous Period Value}} \times 100$
- **Zero Baseline Rule:** If the previous period has 0 value or no records exist, percentage change is returned as `null` with status `"insufficient_data"`. No growth percentage is fabricated.

### 2.8 Customer RFM Segmentation
- **Description:** Classification of customers based on purchase recency, frequency, and monetary spend:
  - **Champions:** $\ge 3$ orders, total spend $> ₹5,000$, last order within 30 days.
  - **Loyal Customers:** $\ge 2$ orders, last order within 60 days.
  - **At Risk:** $> 60$ days since last order.
  - **New / One-Time:** 1 completed order.
