/**
 * Ecomlytics — Frontend Application Engine.
 * Multi-tenant, authenticated, verified analytics client.
 */

const API = "/api";

function getUserSession() {
  const raw = localStorage.getItem("ecomlytics_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (e) {
    return null;
  }
}

// Session validation: ensure user is authenticated
async function checkAuthSession() {
  try {
    const r = await fetch(API + "/auth/me", { credentials: "include" });
    if (!r.ok) {
      localStorage.removeItem("ecomlytics_user");
      sessionStorage.removeItem("ecomlytics_token");
      window.location.href = "/login.html";
      return null;
    }
    const user = await r.json();
    const currentStored = getUserSession() || {};
    const workspaces = user.workspaces || [];
    const activeWs = workspaces.find(w => w.id === currentStored.workspace_id) || workspaces[0] || { id: "ws_default", name: "My Store" };
    
    const profile = {
      id: user.id,
      name: user.display_name,
      email: user.email,
      workspace_id: activeWs.id,
      company: activeWs.name,
      workspaces: workspaces,
      plan: "free"
    };
    localStorage.setItem("ecomlytics_user", JSON.stringify(profile));
    return profile;
  } catch (err) {
    localStorage.removeItem("ecomlytics_user");
    sessionStorage.removeItem("ecomlytics_token");
    window.location.href = "/login.html";
    return null;
  }
}

async function api(path, options = {}) {
  const token = sessionStorage.getItem("ecomlytics_token");
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) {
    headers["Authorization"] = "Bearer " + token;
  }
  const u = getUserSession();
  if (u && u.workspace_id) {
    headers["X-Workspace-ID"] = u.workspace_id;
  }

  const r = await fetch(API + path, {
    ...options,
    headers: headers,
    credentials: "include"
  });

  if (r.status === 401) {
    localStorage.removeItem("ecomlytics_user");
    sessionStorage.removeItem("ecomlytics_token");
    window.location.href = "/login.html";
    throw new Error("Unauthorized");
  }

  if (!r.ok) {
    const errData = await r.json().catch(() => ({}));
    throw new Error(errData.detail || "API request failed: " + r.status);
  }

  return r.json();
}

async function signOut() {
  try {
    await fetch(API + "/auth/logout", { method: "POST", credentials: "include" });
  } catch (e) {}
  localStorage.removeItem("ecomlytics_user");
  sessionStorage.removeItem("ecomlytics_token");
  window.location.href = "/login.html";
}

const fmt = n => new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(n || 0);
const money = n => "₹" + new Intl.NumberFormat("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n || 0);

function shell(active) {
  const u = getUserSession() || { name: "Analytics User", company: "My Store", email: "user@store.com" };
  const initials = u.name ? u.name.split(" ").map(w => w[0]).join("").substring(0, 2).toUpperCase() : "US";

  document.querySelector(".app").innerHTML = `
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-mark">E</div>
      Ecom<span>lytics</span>
    </div>

    <div class="nav-label">${escapeHtml(u.company || u.name + "'s Store")}</div>

    <nav class="nav">
      <a href="/index.html" class="${active === "overview" ? "active" : ""}">
        <span class="ico">⌂</span>Overview
      </a>
      <a href="/pages/sales.html" class="${active === "sales" ? "active" : ""}">
        <span class="ico">◈</span>Sales Analytics
      </a>
      <a href="/pages/products.html" class="${active === "products" ? "active" : ""}">
        <span class="ico">▦</span>Product Intelligence
      </a>
      <a href="/pages/customers.html" class="${active === "customers" ? "active" : ""}">
        <span class="ico">◉</span>Customer Intelligence
      </a>
      <a href="/pages/retention.html" class="${active === "retention" ? "active" : ""}">
        <span class="ico">↗</span>Retention & Funnel
      </a>
      <a href="/pages/insights.html" class="${active === "insights" ? "active" : ""}">
        <span class="ico">✦</span>Business Insights
      </a>
      <a href="/pages/data-sources.html" class="${active === "data-sources" ? "active" : ""}">
        <span class="ico">⊞</span>Data Sources
      </a>
    </nav>

    <div class="nav-label">Platform</div>
    <nav class="nav">
      <a href="/pages/subscription.html" class="${active === "subscription" ? "active" : ""}">
        <span class="ico">◇</span>Plans & Billing
      </a>
    </nav>

    <div class="sidebar-footer">
      <div style="font-weight:700;color:#e2e8f0;font-size:12px;overflow:hidden;text-overflow:ellipsis">${escapeHtml(u.name)}</div>
      <div style="font-size:10px;color:#94a3b8;margin-bottom:8px">${escapeHtml(u.email)}</div>
      <span class="status-dot"></span><span style="font-size:11px">Engine Online</span>
      <br>
      <a href="#" onclick="signOut();return false;" style="display:inline-block;margin-top:8px;color:#cbd5e1;font-size:11px">Sign out</a>
    </div>
  </aside>

  <main class="main" id="content">
    <div style="padding:40px;text-align:center;color:#64748b">Loading analytics workspace...</div>
  </main>`;
}

function header(title, sub) {
  const u = getUserSession() || { name: "User" };
  const initials = u.name ? u.name.split(" ").map(w => w[0]).join("").substring(0, 2).toUpperCase() : "US";
  return `
  <div class="top">
    <div class="title">
      <h1>${escapeHtml(title)}</h1>
      <p>${escapeHtml(sub)}</p>
    </div>
    <div class="top-right">
      <div class="badge">Workspace: ${escapeHtml(u.company || "Store")}</div>
      <div class="profile" title="${escapeHtml(u.email || '')}">${initials}</div>
    </div>
  </div>`;
}

function escapeHtml(s) {
  if (!s) return "";
  return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

function renderDelta(m) {
  if (!m || m.change_pct === null || m.change_pct === undefined) {
    return `<div class="delta note">Not enough data for period comparison</div>`;
  }
  const isUp = m.change_pct >= 0;
  const arrow = isUp ? "↑" : "↓";
  const cls = isUp ? "up" : "down";
  return `<div class="delta ${cls}">${arrow} ${Math.abs(m.change_pct)}% vs previous 30d</div>`;
}

// ============================================================
// PAGE: OVERVIEW
// ============================================================
async function overviewPage() {
  shell("overview");
  await checkAuthSession();
  const content = document.getElementById("content");

  try {
    const o = await api("/overview");

    if (o.status === "no_data") {
      content.innerHTML = header("Analytics Overview", "High-level summary of your store's performance") + `
      <div class="empty-state">
        <div class="empty-state-icon">📊</div>
        <h3>No Store Data Loaded Yet</h3>
        <p>Your workspace is fresh and has no imported orders or products. Import your CSV records or connect a source to see real revenue, conversion, and retention metrics.</p>
        <a class="btn" href="/pages/data-sources.html">Go to Data Sources & Import CSV</a>
      </div>`;
      return;
    }

    const cmp = o.comparison ? o.comparison.metrics : {};

    content.innerHTML = header("Analytics Overview", "High-level summary of your store's performance") + `
    <div class="grid kpis">
      <div class="card kpi">
        <div class="label">Total Revenue</div>
        <div class="value">${money(o.revenue)}</div>
        ${renderDelta(cmp.revenue)}
      </div>
      <div class="card kpi">
        <div class="label">Completed Orders</div>
        <div class="value">${fmt(o.orders)}</div>
        ${renderDelta(cmp.orders)}
      </div>
      <div class="card kpi">
        <div class="label">Average Order Value (AOV)</div>
        <div class="value">${money(o.aov)}</div>
        ${renderDelta(cmp.aov)}
      </div>
      <div class="card kpi">
        <div class="label">Repeat Customer Rate</div>
        <div class="value">${o.repeat_rate}%</div>
        ${renderDelta(cmp.repeat_rate)}
      </div>
    </div>

    <div class="grid two" style="margin-top:20px">
      <div class="card">
        <div class="section-title">Order Performance Summary</div>
        <div class="grid two" style="margin-top:10px">
          <div>
            <div style="color:#64748b;font-size:12px">Total Units Sold</div>
            <div style="font-size:22px;font-weight:700;margin-top:4px">${fmt(o.units)}</div>
          </div>
          <div>
            <div style="color:#64748b;font-size:12px">Return Rate</div>
            <div style="font-size:22px;font-weight:700;margin-top:4px;color:${o.return_rate > 15 ? '#d64545' : '#18a86b'}">${o.return_rate}%</div>
          </div>
          <div>
            <div style="color:#64748b;font-size:12px">Total Catalog Products</div>
            <div style="font-size:22px;font-weight:700;margin-top:4px">${fmt(o.products)}</div>
          </div>
          <div>
            <div style="color:#64748b;font-size:12px">Gross Profit (Tracked)</div>
            <div style="font-size:22px;font-weight:700;margin-top:4px">${money(o.profit)}</div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="section-title">Data Lineage & Freshness</div>
        <p class="note" style="margin-bottom:12px">Every figure above is dynamically calculated from verified workspace database records. No numbers are fabricated or estimated.</p>
        <div style="font-size:12px;margin-bottom:8px"><strong>Workspace ID:</strong> <span class="pill">${escapeHtml(getUserSession().workspace_id)}</span></div>
        <div style="font-size:12px;margin-bottom:8px"><strong>Period Basis:</strong> Most recent 30-day window comparison</div>
        <div style="margin-top:14px"><a class="btn" href="/pages/data-sources.html" style="padding:7px 12px;font-size:11px">Manage Data Sources</a></div>
      </div>
    </div>`;
  } catch (err) {
    content.innerHTML = `<div class="card"><div class="section-title">Error Loading Overview</div><p class="note">${escapeHtml(err.message)}</p></div>`;
  }
}

// ============================================================
// PAGE: SALES
// ============================================================
async function salesPage() {
  shell("sales");
  await checkAuthSession();
  const content = document.getElementById("content");

  try {
    const [salesData, overviewData] = await Promise.all([api("/sales"), api("/overview")]);
    const trend = salesData.sales_trend || [];

    if (!trend.length) {
      content.innerHTML = header("Sales Analytics", "Detailed breakdown of sales and revenue trends") + `
      <div class="empty-state">
        <div class="empty-state-icon">📈</div>
        <h3>No Sales Records Found</h3>
        <p>No completed order records are currently associated with this workspace. Import an orders CSV to analyze revenue trends.</p>
        <a class="btn" href="/pages/data-sources.html">Import Orders CSV</a>
      </div>`;
      return;
    }

    content.innerHTML = header("Sales Analytics", "Detailed breakdown of sales and revenue trends") + `
    <div class="grid three" style="margin-bottom:20px">
      <div class="card kpi">
        <div class="label">Total Gross Sales</div>
        <div class="value">${money(overviewData.revenue)}</div>
      </div>
      <div class="card kpi">
        <div class="label">Total Orders</div>
        <div class="value">${fmt(overviewData.orders)}</div>
      </div>
      <div class="card kpi">
        <div class="label">Average Basket Size</div>
        <div class="value">${money(overviewData.aov)}</div>
      </div>
    </div>

    <div class="card">
      <div class="section-title">Daily Sales Trend (Recent Periods)</div>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>Date</th><th>Completed Orders</th><th>Units Sold</th><th>Daily Revenue</th></tr>
          </thead>
          <tbody>
            ${trend.map(t => `
              <tr>
                <td><b>${t.order_date}</b></td>
                <td>${fmt(t.orders)}</td>
                <td>${fmt(t.units)}</td>
                <td><b>${money(t.revenue)}</b></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </div>`;
  } catch (err) {
    content.innerHTML = `<div class="card"><div class="section-title">Error Loading Sales Analytics</div><p class="note">${escapeHtml(err.message)}</p></div>`;
  }
}

// ============================================================
// PAGE: PRODUCTS
// ============================================================
async function productsPage() {
  shell("products");
  await checkAuthSession();
  const content = document.getElementById("content");

  try {
    const prods = await api("/products");

    if (!prods.length) {
      content.innerHTML = header("Product Intelligence", "Performance, margins, and sales by product") + `
      <div class="empty-state">
        <div class="empty-state-icon">📦</div>
        <h3>No Products in Catalog</h3>
        <p>Your workspace has no products catalog. Import a products CSV to analyze category distribution, gross margins, and units sold.</p>
        <a class="btn" href="/pages/data-sources.html">Import Products CSV</a>
      </div>`;
      return;
    }

    content.innerHTML = header("Product Intelligence", "Performance, margins, and sales by product") + `
    <div class="card">
      <div class="section-title">Product Catalog & Revenue Contribution (${prods.length} items)</div>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>Product Name</th><th>Category</th><th>Unit Price</th><th>Cost</th><th>Gross Margin</th><th>Units Sold</th><th>Total Revenue</th><th>Return Rate</th></tr>
          </thead>
          <tbody>
            ${prods.map(p => `
              <tr>
                <td><b>${escapeHtml(p.name)}</b></td>
                <td><span class="pill">${escapeHtml(p.category || 'General')}</span></td>
                <td>${money(p.price)}</td>
                <td>${money(p.cost)}</td>
                <td><b>${p.margin}%</b></td>
                <td>${fmt(p.units_sold)}</td>
                <td><b>${money(p.revenue)}</b></td>
                <td style="color:${p.return_rate > 15 ? '#d64545' : '#18a86b'}">${p.return_rate}%</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </div>`;
  } catch (err) {
    content.innerHTML = `<div class="card"><div class="section-title">Error Loading Product Intelligence</div><p class="note">${escapeHtml(err.message)}</p></div>`;
  }
}

// ============================================================
// PAGE: CUSTOMERS
// ============================================================
async function customersPage() {
  shell("customers");
  await checkAuthSession();
  const content = document.getElementById("content");

  try {
    const segData = await api("/customers/segments");
    const summary = segData.summary || {};
    const segments = segData.segments || {};
    const totalCustomers = Object.values(summary).reduce((a, b) => a + b, 0);

    if (totalCustomers === 0) {
      content.innerHTML = header("Customer Intelligence", "Customer behavior, RFM segmentation, and lifetime value") + `
      <div class="empty-state">
        <div class="empty-state-icon">👥</div>
        <h3>No Customer Records Found</h3>
        <p>No customer records are currently loaded for this workspace. Import a customers CSV or orders CSV to generate segments.</p>
        <a class="btn" href="/pages/data-sources.html">Import Customers CSV</a>
      </div>`;
      return;
    }

    content.innerHTML = header("Customer Intelligence", "Customer behavior, RFM segmentation, and lifetime value") + `
    <div class="grid four" style="margin-bottom:20px">
      <div class="card kpi">
        <div class="label">Champions</div>
        <div class="value">${summary["Champions"] || 0}</div>
        <div class="delta up">High spend & high frequency</div>
      </div>
      <div class="card kpi">
        <div class="label">Loyal Customers</div>
        <div class="value">${summary["Loyal Customers"] || 0}</div>
        <div class="delta up">Frequent repeat buyers</div>
      </div>
      <div class="card kpi">
        <div class="label">At Risk</div>
        <div class="value" style="color:#d64545">${summary["At Risk"] || 0}</div>
        <div class="delta down">> 60 days since last purchase</div>
      </div>
      <div class="card kpi">
        <div class="label">One-Time Buyers</div>
        <div class="value">${summary["One-Time Buyers"] || 0}</div>
        <div class="delta note">Single purchase to date</div>
      </div>
    </div>

    <div class="card">
      <div class="section-title">Customer RFM Breakdown</div>
      <p class="note" style="margin-bottom:14px">Customers are classified dynamically based on recency, frequency, and total monetary value from completed orders.</p>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>Customer Name</th><th>Email</th><th>City</th><th>Segment</th><th>Total Spend</th><th>Completed Orders</th></tr>
          </thead>
          <tbody>
            ${Object.entries(segments).flatMap(([segName, custs]) => 
              custs.slice(0, 5).map(c => `
                <tr>
                  <td><b>${escapeHtml(c.name)}</b></td>
                  <td>${escapeHtml(c.email || '—')}</td>
                  <td>${escapeHtml(c.city || '—')}</td>
                  <td><span class="pill ${segName === 'Champions' ? 'good' : (segName === 'At Risk' ? 'danger' : '')}">${segName}</span></td>
                  <td><b>${money(c.total_spend)}</b></td>
                  <td>${fmt(c.orders)}</td>
                </tr>
              `)
            ).join("")}
          </tbody>
        </table>
      </div>
    </div>`;
  } catch (err) {
    content.innerHTML = `<div class="card"><div class="section-title">Error Loading Customer Intelligence</div><p class="note">${escapeHtml(err.message)}</p></div>`;
  }
}

// ============================================================
// PAGE: RETENTION & FUNNELS
// ============================================================
async function retentionPage() {
  shell("retention");
  await checkAuthSession();
  const content = document.getElementById("content");

  try {
    const [funnelData, cohortData] = await Promise.all([api("/funnels"), api("/cohorts")]);

    content.innerHTML = header("Retention & Funnel Analysis", "Event-driven conversion journeys and acquisition retention cohorts") + `
    <!-- 1. Funnel Analysis Section -->
    <div class="card" style="margin-bottom:24px">
      <div class="section-title">${escapeHtml(funnelData.funnel_name || "Store Purchase Funnel")}</div>
      ${funnelData.status === "insufficient_data" ? `
        <div class="empty-state" style="padding:28px 16px;margin:10px 0">
          <p class="note">${escapeHtml(funnelData.message)}</p>
          <button class="btn" onclick="seedSampleFunnelEvents()">Simulate Test Event Stream</button>
        </div>
      ` : `
        <p class="note" style="margin-bottom:16px">Multi-step user progression. Steps must occur in chronological order within the conversion window.</p>
        <div class="grid two">
          <div>
            ${funnelData.stages.map((s, i) => {
              const maxVal = funnelData.stages[0].count || 1;
              const widthPct = Math.max(8, (s.count / maxVal) * 100);
              return `
              <div class="funnel-row">
                <div class="funnel-head">
                  <span><b>Step ${i + 1}: ${escapeHtml(s.name)}</b></span>
                  <span><b>${fmt(s.count)} users</b></span>
                </div>
                <div class="bar">
                  <i style="width:${widthPct}%"></i>
                </div>
                <div style="font-size:11px;color:#64748b;margin-top:4px">
                  ${i === 0 ? "Top of Funnel Entry" : `${((s.count / (funnelData.stages[i - 1].count || 1)) * 100).toFixed(1)}% step conversion`}
                </div>
              </div>`;
            }).join("")}
          </div>
          <div style="border-left:1px solid #edf0f5;padding-left:20px">
            <div style="font-weight:700;font-size:13px;margin-bottom:12px">Conversion & Drop-off Summary</div>
            <div style="font-size:26px;font-weight:800;color:#18a86b">${funnelData.overall_conversion}%</div>
            <div class="note">Overall End-to-End Conversion Rate</div>
            <div style="margin-top:16px">
              ${Object.entries(funnelData.dropoffs || {}).map(([stepKey, drop]) => `
                <div style="font-size:12px;margin-bottom:8px">
                  <span style="color:#64748b">${escapeHtml(stepKey)}:</span> 
                  <b style="color:#d64545">${drop.rate}% drop-off</b> (${drop.count} users)
                </div>
              `).join("")}
            </div>
          </div>
        </div>
      `}
    </div>

    <!-- 2. Customer Cohort Retention Matrix -->
    <div class="card">
      <div class="section-title">Customer Acquisition Cohort Retention</div>
      ${cohortData.status === "insufficient_data" ? `
        <div class="empty-state" style="padding:28px 16px;margin:10px 0">
          <p class="note">${escapeHtml(cohortData.message)}</p>
        </div>
      ` : `
        <p class="note" style="margin-bottom:12px">Cohorts group customers by the month of their first completed purchase (Month 0 = 100%). Each column shows the % of that cohort returning to make subsequent purchases.</p>
        <div class="cohort-matrix-wrap">
          <table class="cohort-table">
            <thead>
              <tr>
                <th style="text-align:left;padding-left:14px">Cohort Month</th>
                <th>Customers</th>
                ${cohortData.period_labels.map(l => `<th>${escapeHtml(l)}</th>`).join("")}
              </tr>
            </thead>
            <tbody>
              ${cohortData.cohorts.map(c => `
                <tr>
                  <td class="cohort-label">${escapeHtml(c.cohort_month)}</td>
                  <td><b>${fmt(c.cohort_size)}</b></td>
                  ${c.periods.map(p => {
                    const alpha = Math.max(0.12, p.retention_rate / 100);
                    const bg = `rgba(24, 168, 107, ${alpha})`;
                    const color = p.retention_rate > 50 ? "#ffffff" : "#1e293b";
                    return `
                    <td>
                      <div class="cohort-cell ${p.is_incomplete ? 'incomplete' : ''}" style="background:${bg};color:${color}" title="Cohort ${c.cohort_month}: ${p.retained_customers} / ${c.cohort_size} (${p.retention_rate}%)">
                        ${p.retention_rate}%
                      </div>
                    </td>`;
                  }).join("")}
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `}
    </div>`;
  } catch (err) {
    content.innerHTML = `<div class="card"><div class="section-title">Error Loading Retention & Funnels</div><p class="note">${escapeHtml(err.message)}</p></div>`;
  }
}

async function seedSampleFunnelEvents() {
  try {
    const events = [
      { event_name: "product_view", session_id: "s1" },
      { event_name: "add_to_cart", session_id: "s1" },
      { event_name: "checkout_started", session_id: "s1" },
      { event_name: "purchase_completed", session_id: "s1" },
      { event_name: "product_view", session_id: "s2" },
      { event_name: "add_to_cart", session_id: "s2" },
      { event_name: "product_view", session_id: "s3" }
    ];
    for (const ev of events) {
      await api("/events", { method: "POST", body: JSON.stringify(ev) });
    }
    retentionPage();
  } catch (err) {
    alert("Could not seed test events: " + err.message);
  }
}

// ============================================================
// PAGE: INSIGHTS
// ============================================================
async function insightsPage() {
  shell("insights");
  await checkAuthSession();
  const content = document.getElementById("content");

  try {
    const data = await api("/insights");
    const insights = data.insights || [];

    if (!insights.length) {
      content.innerHTML = header("Business Insights", "Algorithmic decision support and automated findings") + `
      <div class="empty-state">
        <div class="empty-state-icon">💡</div>
        <h3>No Insights Available</h3>
        <p>Your store needs order and product data before our automated insight engine can detect revenue opportunities or return rate warnings.</p>
        <a class="btn" href="/pages/data-sources.html">Import Store Data</a>
      </div>`;
      return;
    }

    content.innerHTML = header("Business Insights", "Algorithmic decision support and automated findings") + `
    <div class="card">
      <div class="section-title">Automated Decision Support (${insights.length} recommendations)</div>
      ${insights.map(ins => `
        <div class="insight ${ins.type === 'warning' ? 'high' : (ins.type === 'opportunity' ? 'medium' : '')}">
          <h3>${escapeHtml(ins.title)}</h3>
          <p>${escapeHtml(ins.detail)}</p>
        </div>
      `).join("")}
    </div>`;
  } catch (err) {
    content.innerHTML = `<div class="card"><div class="section-title">Error Loading Insights</div><p class="note">${escapeHtml(err.message)}</p></div>`;
  }
}

// ============================================================
// PAGE: DATA SOURCES & CSV IMPORT
// ============================================================
async function dataSourcesPage() {
  shell("data-sources");
  await checkAuthSession();
  const content = document.getElementById("content");

  try {
    const [sources, importJobs] = await Promise.all([api("/data-sources"), api("/imports")]);

    content.innerHTML = header("Data Sources & Integrations", "Import CSV files and monitor analytics synchronization") + `
    <!-- CSV Upload Card -->
    <div class="card" style="margin-bottom:24px">
      <div class="section-title">Import Store CSV Dataset</div>
      <p class="note" style="margin-bottom:16px">Upload your orders, products, or customer CSV records. Duplicate external IDs are safely skipped to prevent metric inflation.</p>
      
      <div style="display:flex;gap:12px;margin-bottom:14px;align-items:center">
        <label style="font-size:12px;font-weight:700;color:#334155">Dataset Type:</label>
        <select id="csvDatasetType" class="select" style="font-size:12px;padding:8px 12px">
          <option value="orders">Orders (orders.csv)</option>
          <option value="products">Products (products.csv)</option>
          <option value="customers">Customers (customers.csv)</option>
        </select>
      </div>

      <div class="dropzone" id="csvDropzone" onclick="document.getElementById('csvFileInput').click()">
        <div class="dropzone-icon">📁</div>
        <div class="dropzone-text">Click or drag & drop a CSV file here to upload</div>
        <div class="dropzone-sub">Supported formats: .csv (UTF-8)</div>
      </div>
      <input type="file" id="csvFileInput" accept=".csv" style="display:none" onchange="handleCsvFileSelected(this.files[0])">
      <div id="importResultMsg" style="margin-top:12px;display:none"></div>
    </div>

    <!-- Active Data Sources Status -->
    <div class="card" style="margin-bottom:24px">
      <div class="section-title">Connected Data Sources</div>
      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr><th>Source Name</th><th>Status</th><th>Status Message</th><th>Last Synced</th></tr>
          </thead>
          <tbody>
            ${sources.map(s => {
              const stateClass = s.state === 'connected' ? 'ok' : (s.state === 'stub_mode' ? 'info' : 'warn');
              return `
              <tr>
                <td><b>${escapeHtml(s.name)}</b></td>
                <td><span class="source-state ${stateClass}">${escapeHtml(s.state)}</span></td>
                <td>${escapeHtml(s.message || '—')}</td>
                <td>${s.last_synced ? new Date(s.last_synced).toLocaleString() : '—'}</td>
              </tr>`;
            }).join("")}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Import Job History -->
    <div class="card">
      <div class="section-title">Import History</div>
      ${!importJobs.length ? `<div class="empty">No import jobs recorded yet.</div>` : `
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr><th>Job ID</th><th>Type</th><th>File</th><th>Status</th><th>Processed</th><th>Imported</th><th>Skipped</th><th>Date</th></tr>
            </thead>
            <tbody>
              ${importJobs.map(j => `
                <tr>
                  <td><b>${escapeHtml(j.id)}</b></td>
                  <td><span class="pill">${escapeHtml(j.dataset_type)}</span></td>
                  <td>${escapeHtml(j.filename)}</td>
                  <td><span class="import-badge ${j.status === 'completed' ? 'completed' : (j.status === 'failed' ? 'failed' : 'warnings')}">${escapeHtml(j.status)}</span></td>
                  <td>${j.total_rows}</td>
                  <td><b>${j.imported_rows}</b></td>
                  <td>${j.skipped_rows}</td>
                  <td>${new Date(j.created_at).toLocaleString()}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `}
    </div>`;

    setupDropzone();
  } catch (err) {
    content.innerHTML = `<div class="card"><div class="section-title">Error Loading Data Sources</div><p class="note">${escapeHtml(err.message)}</p></div>`;
  }
}

function setupDropzone() {
  const dropzone = document.getElementById("csvDropzone");
  if (!dropzone) return;

  ["dragenter", "dragover"].forEach(eventName => {
    dropzone.addEventListener(eventName, e => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    }, false);
  });

  ["dragleave", "drop"].forEach(eventName => {
    dropzone.addEventListener(eventName, e => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    }, false);
  });

  dropzone.addEventListener("drop", e => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length) handleCsvFileSelected(files[0]);
  });
}

async function handleCsvFileSelected(file) {
  if (!file) return;
  const msgEl = document.getElementById("importResultMsg");
  const datasetType = document.getElementById("csvDatasetType").value;

  msgEl.style.display = "block";
  msgEl.innerHTML = `<div class="pill info">Reading and importing ${escapeHtml(file.name)}...</div>`;

  const reader = new FileReader();
  reader.onload = async function(e) {
    const text = e.target.result;
    try {
      const res = await api("/imports", {
        method: "POST",
        body: JSON.stringify({
          dataset_type: datasetType,
          csv_content: text,
          filename: file.name
        })
      });

      const sm = res.import_summary;
      msgEl.innerHTML = `
      <div class="card" style="background:#f0fdf4;border:1px solid #bbf7d0;padding:14px;margin-top:10px">
        <strong style="color:#15803d">✓ Import Succeeded: ${escapeHtml(sm.status)}</strong>
        <div style="font-size:12px;color:#166534;margin-top:4px">
          Processed: ${sm.total_rows} | Imported: <b>${sm.imported_rows}</b> | Skipped Duplicates: ${sm.skipped_rows} | Rejected: ${sm.rejected_rows}
        </div>
      </div>`;
      setTimeout(() => dataSourcesPage(), 1500);
    } catch (err) {
      msgEl.innerHTML = `<div class="pill danger" style="padding:10px">Import Failed: ${escapeHtml(err.message)}</div>`;
    }
  };
  reader.readAsText(file);
}

// ============================================================
// PAGE: SUBSCRIPTION
// ============================================================
async function subscriptionPage() {
  shell("subscription");
  await checkAuthSession();
  const content = document.getElementById("content");

  content.innerHTML = header("Plans & Billing", "Choose the right decision intelligence tier for your business") + `
  <div class="billing-hero">
    <div>
      <div class="eyebrow">Enterprise Grade Architecture</div>
      <h2>Upgrade Your Decision Intelligence</h2>
      <p>Unlock cohort retention analysis, automated business insights, and external data integration pipelines.</p>
    </div>
    <div class="billing-status">Current: Free Active</div>
  </div>

  <div class="pricing-grid" style="margin-top:24px">
    <div class="pricing-card current">
      <div class="pricing-top">
        <div class="plan-name">Free Tier</div>
        <p>Essential sales & product analytics for emerging stores.</p>
      </div>
      <div class="price">₹0<small>/month</small></div>
      <div class="pricing-divider"></div>
      <ul class="feature-list">
        <li><span>✓</span> Sales overview & daily trends</li>
        <li><span>✓</span> Product intelligence & margins</li>
        <li><span>✓</span> Customer segmentation</li>
        <li><span>✓</span> Event-driven purchase funnel</li>
      </ul>
      <button class="btn secondary-btn" disabled>Current Active Plan</button>
    </div>

    <div class="pricing-card featured">
      <div class="featured-label">RECOMMENDED</div>
      <div class="pricing-top">
        <div class="plan-name">Pro Pack</div>
        <p>Complete multi-period cohort retention and automated insight intelligence.</p>
      </div>
      <div class="price">₹49<small>/month</small></div>
      <div class="pricing-divider"></div>
      <ul class="feature-list">
        <li><span>✓</span> Everything in Free</li>
        <li><span>✓</span> Customer acquisition cohort matrix</li>
        <li><span>✓</span> Automated AI business insights</li>
        <li><span>✓</span> Unlimited CSV imports & idempotency</li>
        <li><span>✓</span> PostHog & Google Analytics integration</li>
      </ul>
      <button class="btn" onclick="demoCheckout('pro')">Upgrade to Pro Pack</button>
    </div>
  </div>`;
}

async function demoCheckout(plan) {
  try {
    const res = await api("/subscription/checkout", {
      method: "POST",
      body: JSON.stringify({ plan: plan })
    });
    alert(`Success: ${res.message}\nTransaction: ${res.transaction_id}`);
  } catch (err) {
    alert("Checkout error: " + err.message);
  }
}

// ============================================================
// PAGE ROUTER DISPATCH
// ============================================================
const currentPage = document.body.dataset.page;
if (currentPage === "overview") overviewPage();
else if (currentPage === "sales") salesPage();
else if (currentPage === "products") productsPage();
else if (currentPage === "customers") customersPage();
else if (currentPage === "retention") retentionPage();
else if (currentPage === "insights") insightsPage();
else if (currentPage === "data-sources") dataSourcesPage();
else if (currentPage === "subscription") subscriptionPage();