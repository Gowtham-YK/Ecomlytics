/**
 * Ecomlytics unified telemetry.
 * GA4 receives browser events via gtag. Mixpanel, PostHog and Amplitude
 * receive the same authenticated events through the server-side adapter.
 * Provider secrets are never sent to the browser.
 */
(function (window, document) {
  const SESSION_KEY = "ecomlytics_analytics_session";

  function sessionId() {
    try {
      let id = sessionStorage.getItem(SESSION_KEY);
      if (!id) {
        id = (window.crypto && crypto.randomUUID)
          ? crypto.randomUUID()
          : "sess_" + Date.now() + "_" + Math.random().toString(36).slice(2);
        sessionStorage.setItem(SESSION_KEY, id);
      }
      return id;
    } catch (_) {
      return "browser_session";
    }
  }

  function cleanProperties(input) {
    const props = Object.assign({}, input || {});
    ["password", "token", "secret", "authorization", "csv_content", "email"].forEach(k => delete props[k]);
    return props;
  }

  window.identifyUser = function (user) {
    // The backend derives the authenticated identity from the session cookie.
    // This function remains for compatibility with existing app.js calls.
    if (user && user.id) {
      window.__ecomlyticsUserId = String(user.id);
    }
  };

  window.resetUser = function () {
    window.__ecomlyticsUserId = null;
    try { sessionStorage.removeItem(SESSION_KEY); } catch (_) {}
  };

  window.trackProductEvent = function (eventName, properties) {
    const props = cleanProperties(properties);

    // Google Analytics 4 browser-side event collection.
    try {
      if (typeof window.gtag === "function") {
        window.gtag("event", eventName, props);
      }
    } catch (err) {
      console.warn("[GA4] Event dispatch failed:", err);
    }

    // First-party API stores the event and independently forwards it to
    // configured Mixpanel, PostHog and Amplitude projects.
    try {
      fetch("/api/events", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_name: String(eventName),
          session_id: sessionId(),
          properties: props
        })
      }).then(response => {
        if (!response.ok && response.status !== 401) {
          console.warn("[Ecomlytics] Product event was not accepted:", response.status);
        }
      }).catch(err => console.warn("[Ecomlytics] Event forwarding unavailable:", err));
    } catch (err) {
      console.warn("[Ecomlytics] Event dispatch failed:", err);
    }
  };

  window.getFileSizeBucket = function (bytes) {
    if (!bytes || bytes < 50 * 1024) return "<50KB";
    if (bytes < 500 * 1024) return "50KB-500KB";
    if (bytes < 5 * 1024 * 1024) return "500KB-5MB";
    return ">5MB";
  };

  window.getRowCountBucket = function (count) {
    if (!count || count < 25) return "<25";
    if (count < 100) return "25-100";
    if (count < 500) return "100-500";
    return ">500";
  };

  window.sanitizeError = function (msg) {
    if (!msg) return "unknown_error";
    const lower = String(msg).toLowerCase();
    if (lower.includes("column") || lower.includes("header") || lower.includes("missing")) return "invalid_csv_schema";
    if (lower.includes("duplicate")) return "duplicate_records";
    if (lower.includes("auth") || lower.includes("unauthorized") || lower.includes("forbidden")) return "authorization_error";
    if (lower.includes("network") || lower.includes("connection")) return "network_error";
    return "general_error";
  };
})(window, document);
