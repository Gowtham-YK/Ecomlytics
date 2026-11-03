# Ecomlytics — Cohort & Customer Retention Analysis Specification (Stage I)

**Document Reference:** Section 9 of Ecomlytics Master Implementation Specification  
**Version:** 2.0.0  
**Date:** October 31, 2026  

---

## 1. Cohort Definitions & Semantics

Ecomlytics implements **Customer Acquisition Purchase Cohorts**:
- **Anchor Event:** Customer's first qualifying completed order date.
- **Cohort Granularity:** Monthly acquisition period ($YYYY-MM$).
- **Cohort Size ($N_0$):** Count of distinct customers who made their first purchase in that calendar month.
- **Return Action:** Customer completes another order in month $M+k$ ($k \ge 1$).

---

## 2. Retention Matrix Structure

| Cohort Month | Cohort Size | Month 0 ($M_0$) | Month 1 ($M_1$) | Month 2 ($M_2$) | Month 3 ($M_3$) |
|---|---|---|---|---|---|
| **2026-07** | $C_{07}$ | 100% ($C_{07}$) | $R_1 / C_{07}$ | $R_2 / C_{07}$ | $R_3 / C_{07}$ |
| **2026-08** | $C_{08}$ | 100% ($C_{08}$) | $R_1 / C_{08}$ | $R_2 / C_{08}$ | — |
| **2026-09** | $C_{09}$ | 100% ($C_{09}$) | $R_1 / C_{09}$ | — | — |
| **2026-10** (Current) | $C_{10}$ | 100% ($C_{10}$) | — | — | — |

---

## 3. Mathematical Rules & Denominators

1. **Unique Customer Count:** A customer making multiple purchases in Month $k$ is counted exactly once in Month $k$.
2. **Retention Rate Formula:**
   $$\text{Retention Rate}(M, k) = \frac{\text{Count of unique customers in cohort } M \text{ with } \ge 1 \text{ completed order in month } M+k}{\text{Total customers in cohort } M} \times 100$$
3. **Current Incomplete Period:**
   - Any period corresponding to the current unfinished month is flagged with `is_incomplete: true`.
4. **Honest Empty State:**
   - If a workspace has 0 orders, or orders span fewer than 2 monthly cohorts, the engine reports `status: "insufficient_data"` with an honest advisory rather than fabricating flat mock percentages.
