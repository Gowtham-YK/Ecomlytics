/**
 * Ecomlytics Product Telemetry & Analytics Module (PostHog & GA4)
 * Measures platform adoption, user funnels, and feature usage.
 * Privacy-first: masks sensitive inputs, excludes customer data/passwords.
 */

(function (window, document) {
  // 1. Official PostHog Web SDK snippet
  !(function (t, e) {
    var o, n, p, r;
    e.__SV ||
      ((window.posthog = e),
      (e._i = []),
      (e.init = function (i, s, a) {
        function g(t, e) {
          var o = e.split(".");
          2 == o.length && ((t = t[o[0]]), (e = o[1])),
            (t[e] = function () {
              t.push([e].concat(Array.prototype.slice.call(arguments, 0)));
            });
        }
        ((p = t.createElement("script")).type = "text/javascript"),
          (p.crossOrigin = "anonymous"),
          (p.async = !0),
          (p.src =
            s.api_host.replace(".i.posthog.com", "-assets.i.posthog.com") +
            "/static/array.js"),
          (r = t.getElementsByTagName("script")[0]).parentNode.insertBefore(
            p,
            r
          );
        var u = e;
        for (
          void 0 !== a ? (u = e[a] = []) : (a = "posthog"),
            u.people = u.people || [],
            u.toString = function (t) {
              var e = "posthog";
              return "posthog" !== a && (e += "." + a), t || (e += " (stub)"), e;
            },
            u.people.toString = function () {
              return u.toString(1) + ".people (stub)";
            },
            o =
              "init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey getNextSurveyStep identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug".split(
                " "
              ),
            n = 0;
          n < o.length;
          n++
        )
          g(u, o[n]);
        e._i.push([i, s, a]);
      }),
      (e.__SV = 1.0));
  })(document, window.posthog || []);

  let isInitialized = false;

  // Initialize PostHog from API or local fallback
  async function initPostHog() {
    if (isInitialized) return;

    let token = null;
    let host = "https://us.i.posthog.com";

    try {
      const resp = await fetch("/api/telemetry/config");
      if (resp.ok) {
        const cfg = await resp.json();
        if (cfg.posthog_enabled && cfg.posthog_token) {
          token = cfg.posthog_token;
          host = cfg.posthog_host || host;
        }
      }
    } catch (e) {
      // Offline or network error - continue silently
    }

    // Fallback to configured token if API unavailable
    if (!token && window.__POSTHOG_TOKEN__) {
      token = window.__POSTHOG_TOKEN__;
      host = window.__POSTHOG_HOST__ || host;
    }

    if (!token) {
      console.log("[Telemetry] PostHog not configured (stub mode active).");
      return;
    }

    try {
      window.posthog.init(token, {
        api_host: host,
        person_profiles: "identified_only", // Privacy: do not create anonymous profiles
        autocapture: false, // Explicit events preferred over noisy autocapture
        capture_pageview: true, // Record page view once per navigation
        session_recording: {
          maskAllInputs: true, // Privacy: mask text & inputs in session replays
          maskTextSelector: ".sensitive, [data-sensitive], input, textarea"
        },
        loaded: function (ph) {
          isInitialized = true;
          console.log("[Telemetry] PostHog initialized successfully for Ecomlytics.");
          // Re-associate stored session if user is logged in
          syncStoredSession();
        }
      });
      isInitialized = true;
    } catch (err) {
      console.warn("[Telemetry] PostHog initialization error:", err);
    }
  }

  function syncStoredSession() {
    try {
      const raw = localStorage.getItem("ecomlytics_user");
      if (raw) {
        const u = JSON.parse(raw);
        if (u && u.id) {
          window.identifyUser(u);
        }
      }
    } catch (e) {}
  }

  // Identify authenticated store owner with stable internal user ID (never email as distinct ID)
  window.identifyUser = function (user) {
    if (!user || !user.id) return;
    try {
      if (window.posthog && typeof window.posthog.identify === "function") {
        window.posthog.identify(String(user.id), {
          workspace_id: user.workspace_id || "",
          plan: user.plan || "free",
          role: "owner"
        });
        console.log(`[Telemetry] User identified: ${user.id} (Workspace: ${user.workspace_id})`);
      }
    } catch (e) {
      console.warn("[Telemetry] Identify error:", e);
    }
  };

  // Reset user identity on logout
  window.resetUser = function () {
    try {
      if (window.posthog && typeof window.posthog.reset === "function") {
        window.posthog.reset();
        console.log("[Telemetry] PostHog session reset on logout.");
      }
    } catch (e) {
      console.warn("[Telemetry] Reset error:", e);
    }
  };

  // Safe product event tracking with sanitize & bucketing
  window.trackProductEvent = function (eventName, properties) {
    const props = Object.assign({}, properties || {});

    // Ensure no sensitive credentials, passwords, or tokens leak
    delete props.password;
    delete props.token;
    delete props.secret;
    delete props.authorization;
    delete props.csv_content;

    try {
      if (window.posthog && typeof window.posthog.capture === "function") {
        window.posthog.capture(eventName, props);
        console.log(`[PostHog Event Captured: ${eventName}]`, props);
      }
    } catch (err) {
      console.warn(`[Telemetry] Error capturing ${eventName}:`, err);
    }
  };

  // Helper bucketing functions
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

  // Trigger init on DOM load or immediately
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPostHog);
  } else {
    initPostHog();
  }
})(window, document);

