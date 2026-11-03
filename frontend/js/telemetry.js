/**
 * Ecomlytics Product Telemetry & Analytics Module (PostHog, Mixpanel & GA4)
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

  // 2. Official Mixpanel Web SDK snippet
  !(function (f, b) {
    if (!b.__SV) {
      var e, g, i, h;
      window.mixpanel = b;
      b._i = [];
      b.init = function (e, f, c) {
        function d(a, b) {
          var c = b.split(".");
          2 == c.length && ((a = a[c[0]]), (b = c[1]));
          a[b] = function () {
            a.push([b].concat(Array.prototype.slice.call(arguments, 0)));
          };
        }
        var a = b;
        "undefined" !== typeof c ? (a = b[c] = []) : (c = "mixpanel");
        a.people = a.people || [];
        a.toString = function (a) {
          var d = "mixpanel";
          "mixpanel" !== c && (d += "." + c);
          a || (d += " (stub)");
          return d;
        };
        a.people.toString = function () {
          return a.toString(1) + ".people (stub)";
        };
        i =
          "disable time_event track track_pageview track_links track_forms track_with_groups add_group set_group remove_group register register_once alias unregister identify name_tag set_config reset opt_in_tracking opt_out_tracking has_opted_in_tracking has_opted_out_tracking clear_opt_in_out_tracking start_batch_senders people.set people.set_once people.unset people.increment people.append people.union people.track_charge people.clear_charges people.delete_user people.remove".split(
            " "
          );
        for (h = 0; h < i.length; h++) d(a, i[h]);
        b._i.push([e, f, c]);
      };
      b.__SV = 1.2;
      e = f.createElement("script");
      e.type = "text/javascript";
      e.async = !0;
      e.src = "https://cdn.mxpnl.com/libs/mixpanel-2-latest.min.js";
      g = f.getElementsByTagName("script")[0];
      g.parentNode.insertBefore(e, g);
    }
  })(document, window.mixpanel || []);

  let isInitialized = false;

  // Initialize Telemetry Providers (PostHog & Mixpanel)
  async function initTelemetry() {
    if (isInitialized) return;

    let phToken = null;
    let phHost = "https://us.i.posthog.com";
    let mpToken = null;

    try {
      const resp = await fetch("/api/telemetry/config");
      if (resp.ok) {
        const cfg = await resp.json();
        if (cfg.posthog_enabled && cfg.posthog_token) {
          phToken = cfg.posthog_token;
          phHost = cfg.posthog_host || phHost;
        }
        if (cfg.mixpanel_enabled && cfg.mixpanel_token) {
          mpToken = cfg.mixpanel_token;
        }
      }
    } catch (e) {
      // Offline fallback
    }

    // 1. PostHog Init
    if (phToken) {
      try {
        window.posthog.init(phToken, {
          api_host: phHost,
          person_profiles: "identified_only",
          autocapture: false,
          capture_pageview: true,
          session_recording: {
            maskAllInputs: true,
            maskTextSelector: ".sensitive, [data-sensitive], input, textarea"
          },
          loaded: function () {
            console.log("[Telemetry] PostHog initialized successfully.");
            syncStoredSession();
          }
        });
      } catch (err) {
        console.warn("[Telemetry] PostHog init error:", err);
      }
    }

    // 2. Mixpanel Init
    if (mpToken) {
      try {
        window.mixpanel.init(mpToken, {
          track_pageview: true,
          persistence: "localStorage"
        });
        console.log("[Telemetry] Mixpanel initialized successfully.");
        syncStoredSession();
      } catch (err) {
        console.warn("[Telemetry] Mixpanel init error:", err);
      }
    }

    isInitialized = true;
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

  // Identify authenticated store owner with stable internal user ID
  window.identifyUser = function (user) {
    if (!user || !user.id) return;
    const uid = String(user.id);
    const userProps = {
      workspace_id: user.workspace_id || "",
      plan: user.plan || "free",
      role: "owner"
    };

    // PostHog
    try {
      if (window.posthog && typeof window.posthog.identify === "function") {
        window.posthog.identify(uid, userProps);
      }
    } catch (e) {}

    // Mixpanel
    try {
      if (window.mixpanel && typeof window.mixpanel.identify === "function") {
        window.mixpanel.identify(uid);
        if (window.mixpanel.people && typeof window.mixpanel.people.set === "function") {
          window.mixpanel.people.set(userProps);
        }
      }
    } catch (e) {}

    console.log(`[Telemetry] User identified: ${uid} (Workspace: ${user.workspace_id})`);
  };

  // Reset user identity on logout
  window.resetUser = function () {
    try {
      if (window.posthog && typeof window.posthog.reset === "function") {
        window.posthog.reset();
      }
    } catch (e) {}

    try {
      if (window.mixpanel && typeof window.mixpanel.reset === "function") {
        window.mixpanel.reset();
      }
    } catch (e) {}

    console.log("[Telemetry] Sessions reset on logout.");
  };

  // Unified Product Event Tracking (dispatches to PostHog, Mixpanel, and GA4)
  window.trackProductEvent = function (eventName, properties) {
    const props = Object.assign({}, properties || {});

    // Ensure no sensitive credentials or passwords leak
    delete props.password;
    delete props.token;
    delete props.secret;
    delete props.authorization;
    delete props.csv_content;

    // PostHog Dispatch
    try {
      if (window.posthog && typeof window.posthog.capture === "function") {
        window.posthog.capture(eventName, props);
      }
    } catch (err) {}

    // Mixpanel Dispatch
    try {
      if (window.mixpanel && typeof window.mixpanel.track === "function") {
        window.mixpanel.track(eventName, props);
      }
    } catch (err) {}

    console.log(`[Telemetry Event Captured: ${eventName}]`, props);
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
    document.addEventListener("DOMContentLoaded", initTelemetry);
  } else {
    initTelemetry();
  }
})(window, document);
