# Ecomlytics — Funnel Analysis Specification & Semantics (Stage H)

**Document Reference:** Section 8 of Ecomlytics Master Implementation Specification  
**Version:** 2.0.0  
**Date:** October 31, 2026  

---

## 1. Funnel Definitions & Semantics

Ecomlytics implements two distinct event-driven funnels:

### Funnel 1: Store E-Commerce Purchase Funnel
1. **Product Viewed (`product_view`):** User views a product page.
2. **Add to Cart (`add_to_cart`):** User adds one or more items to their shopping cart.
3. **Checkout Started (`checkout_started`):** User initiates payment checkout.
4. **Purchase Completed (`purchase_completed`):** Transaction completes successfully.

### Funnel 2: Platform Onboarding Funnel
1. **Landing Page (`page_view`):** Visitor lands on Ecomlytics.
2. **Signup Started (`signup_started`):** Visitor opens registration modal/tab.
3. **Registration Completed (`signup_completed`):** Account & workspace created.
4. **Data Import (`csv_import_completed`):** User imports first dataset.
5. **Dashboard Viewed (`dashboard_viewed`):** User inspects live business analytics.

---

## 2. Calculation Rules & Invariants

1. **Unit of Analysis:** Distinct `user_id` or pseudonymous `session_id`.
2. **Step Ordering:** Events must occur in chronological order:
   $$T(\text{Step } 1) \le T(\text{Step } 2) \le T(\text{Step } 3) \le T(\text{Step } 4)$$
3. **Conversion Window:** Default window is 7 days (604,800 seconds) between step 1 and the final step.
4. **Step Conversion Rate:**
   $$\text{Step Conversion Rate}_N = \frac{\text{Unique Users reaching Step } N}{\text{Unique Users reaching Step } N-1} \times 100$$
5. **Overall Conversion Rate:**
   $$\text{Overall Conversion Rate} = \frac{\text{Unique Users reaching Step } \text{Final}}{\text{Unique Users entering Step } 1} \times 100$$
6. **Drop-off Rate:**
   $$\text{Drop-off Count}_N = \text{Step}_{N-1} - \text{Step}_N$$
   $$\text{Drop-off Rate}_N = \frac{\text{Drop-off Count}_N}{\text{Step}_{N-1}} \times 100$$
7. **Empty States:** If zero users enter step 1, the funnel returns `status: "insufficient_data"` with zero values and an explanation of required event instrumentation.
