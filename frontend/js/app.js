const API = "/api";

(function(){
 if(!localStorage.getItem("ecomlytics_user")) window.location.href="/login.html";
})();

const fmt = n => new Intl.NumberFormat("en-IN",{maximumFractionDigits:0}).format(n);
const money = n => "₹" + fmt(n);

const PLAN_META = {
 free: {name:"Free", price:0, advanced:false},
 starter: {name:"Starter", price:999, advanced:true},
 growth: {name:"Growth", price:2999, advanced:true},
 pro: {name:"Pro", price:7999, advanced:true}
};
function currentPlan(){ return localStorage.getItem("ecomlytics_plan") || "free"; }
function planMeta(){ return PLAN_META[currentPlan()] || PLAN_META.free; }
function hasAdvancedAccess(){ return planMeta().advanced === true; }
function upgradeUrl(){ return "/pages/subscription.html"; }
function upgradeBanner(feature){
 if(hasAdvancedAccess()) return "";
 return `<div class="upgrade-banner"><div class="upgrade-icon">✦</div><div class="upgrade-copy"><strong>${feature || "Advanced intelligence"} is available on paid plans</strong><span>You're currently using the Free plan with basic analysis. Upgrade when you need deeper analysis, recommendations and decision intelligence.</span></div><a class="btn upgrade-btn" href="${upgradeUrl()}">View plans</a></div>`;
}
function lockedCard(title, detail, feature="advanced analysis"){
 return `<div class="locked-card"><div class="lock-mark">✦</div><div><span class="pill">Paid plan</span><h3>${title}</h3><p>${detail}</p><a class="btn" href="${upgradeUrl()}">Unlock ${feature}</a></div></div>`;
}

async function api(path){
 const r=await fetch(API+path);
 if(!r.ok) throw new Error("API request failed: "+r.status);
 return r.json();
}

window.addEventListener("error", e => {
 const c=document.getElementById("content");
 if(c && !c.innerHTML.trim()) c.innerHTML='<div class="card"><div class="section-title">Unable to load analytics</div><p class="note">Make sure the FastAPI server is running and refresh this page.</p></div>';
});

function shell(active){
 document.querySelector(".app").innerHTML = `
 <aside class="sidebar">
  <div class="brand"><div class="brand-mark">E</div>Ecom<span>lytics</span></div>

  <div class="nav-label">Workspace</div>

  <nav class="nav">
   <a href="/index.html" class="${active==="overview"?"active":""}">
    <span class="ico">⌂</span>Overview
   </a>

   <a href="/pages/sales.html" class="${active==="sales"?"active":""}">
    <span class="ico">◈</span>Sales Analytics
   </a>

   <a href="/pages/products.html" class="${active==="products"?"active":""}">
    <span class="ico">▦</span>Product Intelligence
   </a>

   <a href="/pages/customers.html" class="${active==="customers"?"active":""}">
    <span class="ico">◉</span>Customer Intelligence
   </a>

   <a href="/pages/retention.html" class="${active==="retention"?"active":""}">
    <span class="ico">↗</span>Retention & Funnel
   </a>

   <a href="/pages/insights.html" class="${active==="insights"?"active":""}">
    <span class="ico">✦</span>Business Insights
   </a>
  </nav>

  <div class="nav-label">Platform</div>

  <nav class="nav">
   <a href="/pages/data-sources.html" class="${active==="data-sources"?"active":""}">
    <span class="ico">⇄</span>Data Sources
   </a>

   <a href="/pages/subscription.html" class="${active==="subscription"?"active":""}">
    <span class="ico">◇</span>Plans & Billing
   </a>

   <a href="#">
    <span class="ico">⚙</span>Settings
   </a>
  </nav>

  <div class="sidebar-footer">
   <span class="status-dot"></span>Analytics engine online
   <br>

   <a href="#"
      onclick="localStorage.removeItem('ecomlytics_user');window.location.href='/login.html';return false;"
      style="display:inline-block;margin-top:8px;color:#aab6ce">
      Sign out
   </a>
  </div>

 </aside>

 <main class="main" id="content"></main>`;
}

function header(title,sub){
 return `
 <div class="top">
  <div class="title">
   <h1>${title}</h1>
   <p>${sub}</p>
  </div>

  <div class="top-right">
   <span class="badge"><span class="status-dot"></span>Demo Data</span>
   <a class="plan-badge ${hasAdvancedAccess()?"paid":"free"}" href="${upgradeUrl()}">${planMeta().name} Plan</a>
   ${hasAdvancedAccess() ? "" : `<a class="upgrade-link" href="${upgradeUrl()}">Upgrade</a>`}
   <div class="profile">GY</div>
  </div>
 </div>`
}

function deltaHtml(m){
 if(!m || m.change_pct===null || m.change_pct===undefined){
  return `<div class="delta note">Not enough data for period comparison</div>`;
 }
 const up = m.change_pct >= 0;
 const arrow = up ? "▲" : "▼";
 const cls = up ? "delta up" : "delta down";
 return `<div class="${cls}">${arrow} ${Math.abs(m.change_pct)}% vs previous ${'30 days'}</div>`;
}

function productRows(products){
 return products.map(p=>`
 <tr>
  <td><b>${p.product_name}</b></td>
  <td>${p.category}</td>
  <td>${fmt(p.views)}</td>
  <td>${fmt(p.units_sold)}</td>
  <td>${money(p.revenue)}</td>
  <td>${p.conversion}%</td>
  <td>${p.rating}</td>
  <td>${p.return_rate}%</td>
 </tr>
 `).join("");
}

async function overviewPage(){

 shell("overview");

 const o=await api("/overview");
 const p=await api("/products");
 const ins=await api("/insights");

 document.getElementById("content").innerHTML=

 header(
  "Overview",
  "A single view of revenue, products, customers and business health"
 )+

 upgradeBanner("Advanced decision intelligence")+

 `
 <div class="grid kpis">

  <div class="card kpi">
   <div class="label">Revenue</div>
   <div class="value">${money(o.revenue)}</div>
   ${deltaHtml(o.comparison && o.comparison.metrics && o.comparison.metrics.revenue)}
  </div>

  <div class="card kpi">
   <div class="label">Orders</div>
   <div class="value">${fmt(o.orders)}</div>
   ${deltaHtml(o.comparison && o.comparison.metrics && o.comparison.metrics.orders)}
  </div>

  <div class="card kpi">
   <div class="label">Average Order Value</div>
   <div class="value">${money(o.aov)}</div>
   ${deltaHtml(o.comparison && o.comparison.metrics && o.comparison.metrics.aov)}
  </div>

  <div class="card kpi">
   <div class="label">Repeat Purchase Rate</div>
   <div class="value">${o.repeat_rate}%</div>
   ${deltaHtml(o.comparison && o.comparison.metrics && o.comparison.metrics.repeat_rate)}
  </div>

 </div>

 <div class="grid two" style="margin-top:18px">

  <div class="card">
   <div class="section-title">Top Products by Revenue</div>

   <div class="table-wrap">

    <table class="table">

     <thead>
      <tr>
       <th>Product</th>
       <th>Category</th>
       <th>Revenue</th>
       <th>Conversion</th>
      </tr>
     </thead>

     <tbody>

      ${
       p
       .sort((a,b)=>b.revenue-a.revenue)
       .slice(0,5)
       .map(x=>`
        <tr>
         <td><b>${x.product_name}</b></td>
         <td>${x.category}</td>
         <td>${money(x.revenue)}</td>
         <td>${x.conversion}%</td>
        </tr>
       `)
       .join("")
      }

     </tbody>

    </table>

   </div>
  </div>

  <div class="card">

   <div class="section-title">What needs attention?</div>

   ${
    ins
    .slice(0,3)
    .map(i=>`
     <div class="insight ${i.priority.toLowerCase()}">
      <h3>${i.title}</h3>
      <p>${i.detail}</p>
     </div>
    `)
    .join("")
   }

  </div>

 </div>

 <div class="grid three" style="margin-top:18px">

  <div class="card">
   <div class="section-title">Catalog</div>
   <div class="value" style="font-size:25px;font-weight:800">
    ${o.products}
   </div>
   <p class="note">Products tracked across the store.</p>
  </div>

  <div class="card">
   <div class="section-title">Units Sold</div>
   <div class="value" style="font-size:25px;font-weight:800">
    ${fmt(o.units)}
   </div>
   <p class="note">Total units represented in the order dataset.</p>
  </div>

  <div class="card">
   <div class="section-title">Return Rate</div>
   <div class="value" style="font-size:25px;font-weight:800">
    ${o.return_rate}%
   </div>
   <p class="note">
    Use returns as a product-quality and expectation signal.
   </p>
  </div>

 </div>
 `;
}

async function salesPage(){

 shell("sales");

 const o=await api("/overview");

 const days=[
  42000,
  51000,
  47000,
  63000,
  59000,
  76000,
  82000,
  79000,
  91000,
  86000,
  103000,
  98000
 ];

 document.getElementById("content").innerHTML=

 header(
  "Sales Analytics",
  "Understand revenue movement, order volume and basket value"
 )+

 upgradeBanner("Advanced sales intelligence")+

 `
 <div class="grid kpis">

  <div class="card kpi">
   <div class="label">Revenue</div>
   <div class="value">${money(o.revenue)}</div>
   <div class="delta">Current dataset</div>
  </div>

  <div class="card kpi">
   <div class="label">Orders</div>
   <div class="value">${fmt(o.orders)}</div>
   <div class="delta">Completed + returned</div>
  </div>

  <div class="card kpi">
   <div class="label">AOV</div>
   <div class="value">${money(o.aov)}</div>
   <div class="delta">Revenue / orders</div>
  </div>

  <div class="card kpi">
   <div class="label">Units</div>
   <div class="value">${fmt(o.units)}</div>
   <div class="delta">Units sold</div>
  </div>

 </div>

 <div class="grid two" style="margin-top:18px">

  <div class="card">

   <div class="section-title">Revenue Trend</div>

   <div class="chart">

    ${
     days.map((v,i)=>`
      <div class="col">

       <div class="barv">
        <i style="height:${Math.round(v/1100)}px"></i>
       </div>

       <small>W${i+1}</small>

      </div>
     `).join("")
    }

   </div>

  </div>

  <div class="card">

   <div class="section-title">Sales Questions</div>

   <div class="insight">
    <h3>Revenue health</h3>
    <p>
     Track whether revenue growth is coming from more customers,
     higher AOV, or increased repeat purchases.
    </p>
   </div>

   <div class="insight">
    <h3>Basket behavior</h3>
    <p>
     AOV can reveal opportunities for bundles,
     cross-sells and threshold-based offers.
    </p>
   </div>

  </div>

 </div>

 <div class="card" style="margin-top:18px">

  <div class="section-title">Business interpretation</div>

  <p class="note">
   Sales Analytics connects revenue and order metrics so operators
   can move from “what happened?” to “what should we investigate?”
  </p>

 </div>
 `;
}

async function productsPage(){

 shell("products");

 const p=await api("/products");

 document.getElementById("content").innerHTML=

 header(
  "Product Intelligence",
  "Find winning products, weak conversion and product-level opportunities"
 )+

 upgradeBanner("Advanced product intelligence")+

 `
 <div class="filters">

  <input
   id="search"
   class="input"
   placeholder="Search products..."
  >

  <select id="cat" class="select">

   <option value="">All categories</option>

   ${
    [...new Set(p.map(x=>x.category))]
    .map(c=>`<option>${c}</option>`)
    .join("")
   }

  </select>

 </div>

 <div class="card">

  <div class="section-title">Product Performance</div>

  <div class="table-wrap">

   <table class="table">

    <thead>

     <tr>
      <th>Product</th>
      <th>Category</th>
      <th>Views</th>
      <th>Units</th>
      <th>Revenue</th>
      <th>Conversion</th>
      <th>Rating</th>
      <th>Returns</th>
     </tr>

    </thead>

    <tbody id="productBody">
     ${productRows(p)}
    </tbody>

   </table>

  </div>

 </div>

 <div class="grid three" style="margin-top:18px">

  <div class="card">
   <div class="section-title">High Traffic / Low Conversion</div>
   <p class="note">
    Identify products attracting attention but failing to convert.
    This is a strong investigation signal.
   </p>
  </div>

  <div class="card">
   <div class="section-title">Margin Opportunities</div>
   <p class="note">
    Compare product revenue with cost to identify products
    contributing meaningful gross margin.
   </p>
  </div>

  <div class="card">
   <div class="section-title">Return Signals</div>
   <p class="note">
    High return rates can point to expectation, quality,
    sizing or fulfillment problems.
   </p>
  </div>

 </div>
 `;

 const render=()=>{

  let q=document
   .getElementById("search")
   .value
   .toLowerCase();

  let c=document
   .getElementById("cat")
   .value;

  document.getElementById("productBody").innerHTML=

   productRows(
    p.filter(x=>
     (!q || x.product_name.toLowerCase().includes(q)) &&
     (!c || x.category===c)
    )
   );
 };

 document.getElementById("search").oninput=render;
 document.getElementById("cat").onchange=render;
}

async function customersPage(){

 shell("customers");

 const d=await api("/customers/segments");

 const colors={
  "Champions":"good",
  "Loyal":"good",
  "Potential Loyalist":"",
  "At Risk":"danger",
  "Lost":"warn"
 };

 document.getElementById("content").innerHTML=

 header(
  "Customer Intelligence",
  "Segment customers by value, recency and relationship"
 )+

 upgradeBanner("Advanced customer intelligence")+

 `
 <div class="grid three">

  ${
   Object.entries(d.counts)
   .map(([k,v])=>`

    <div class="card">

     <div class="section-title">${k}</div>

     <div style="font-size:28px;font-weight:800">
      ${v}
     </div>

     <p class="note">
      Customers in this segment
     </p>

     <span class="pill ${colors[k]||""}">
      ${money(d.spend[k]||0)} spend
     </span>

    </div>

   `)
   .join("")
  }

 </div>

 <div class="card" style="margin-top:18px">

  <div class="section-title">Customer Portfolio</div>

  <div class="table-wrap">

   <table class="table">

    <thead>

     <tr>
      <th>Customer</th>
      <th>City</th>
      <th>Orders</th>
      <th>Total Spend</th>
      <th>Days Since Order</th>
      <th>Segment</th>
     </tr>

    </thead>

    <tbody>

     ${
      d.customers.map(c=>`

       <tr>

        <td><b>${c.customer_name}</b></td>

        <td>${c.city}</td>

        <td>${c.orders}</td>

        <td>${money(c.total_spend)}</td>

        <td>${c.last_order_days}</td>

        <td>
         <span class="pill ${colors[c.segment]||""}">
          ${c.segment}
         </span>
        </td>

       </tr>

      `).join("")
     }

    </tbody>

   </table>

  </div>

 </div>

 <div class="grid two" style="margin-top:18px">

  <div class="card">

   <div class="section-title">RFM-style thinking</div>

   <p class="note">
    Recency shows who is becoming inactive.
    Frequency shows loyalty.
    Monetary value shows customer contribution.
    Together they support targeted retention decisions.
   </p>

  </div>

  <div class="card">

   <div class="section-title">Customer value</div>

   <p class="note">
    Prioritize personalized engagement around Champions
    and reactivation campaigns for At Risk and Lost customers.
   </p>

  </div>

 </div>
 `;
}

async function retentionPage(){

 shell("retention");

 const f=await api("/funnel");

 document.getElementById("content").innerHTML=

 header(
  "Retention & Funnel",
  "Understand where customers drop and how retention changes over time"
 )+

 upgradeBanner("Advanced retention analytics")+

 `
 <div class="grid two">

  <div class="card">

   <div class="section-title">Purchase Funnel</div>

   ${
    f.stages.map((s,i)=>`

     <div class="funnel-row">

      <div class="funnel-head">
       <span>${s.name}</span>
       <b>${fmt(s.value)}</b>
      </div>

      <div class="bar">
       <i style="width:${Math.max(
        8,
        s.value/f.stages[0].value*100
       )}%"></i>
      </div>

      <p class="note">
       ${
        i
        ? ((s.value/f.stages[i-1].value)*100).toFixed(1)
          +"% of previous stage"
        : "Entry volume"
       }
      </p>

     </div>

    `).join("")
   }

  </div>

  <div class="card">

   <div class="section-title">Funnel Diagnosis</div>

   <div class="insight high">

    <h3>Largest opportunity</h3>

    <p>
     Compare each stage's conversion.
     A sharp drop can indicate pricing, UX, trust,
     stock or checkout friction.
    </p>

   </div>

   <div class="insight">

    <h3>Retention lens</h3>

    <p>
     Connect funnel behavior with repeat purchase segments
     to distinguish acquisition problems from loyalty problems.
    </p>

   </div>

  </div>

 </div>

 <div class="grid three" style="margin-top:18px">

  <div class="card">

   <div class="section-title">Week 1 Retention</div>

   <div style="font-size:27px;font-weight:800">
    42%
   </div>

   <p class="note">
    Illustrative cohort view.
   </p>

  </div>

  <div class="card">

   <div class="section-title">Week 4 Retention</div>

   <div style="font-size:27px;font-weight:800">
    27%
   </div>

   <p class="note">
    Illustrative cohort view.
   </p>

  </div>

  <div class="card">

   <div class="section-title">Repeat Purchase</div>

   <div style="font-size:27px;font-weight:800">
    80%
   </div>

   <p class="note">
    Dataset-based customer repeat signal.
   </p>

  </div>

 </div>
 `;
}

async function insightsPage(){

 shell("insights");

 const ins=await api("/insights");

 document.getElementById("content").innerHTML=
 header(
  "Business Insights",
  "Turn metrics into clear explanations and recommended business actions"
 )+
 upgradeBanner("Business decision intelligence")+
 (!hasAdvancedAccess() ? `
  <div class="card" style="margin-top:18px">
   ${lockedCard(
    "Business Insight Engine",
    "The Free plan provides basic KPI analysis. Upgrade to unlock pattern detection, explanations and recommended actions.",
    "insight engine"
   )}
  </div>
 ` : `
  <div class="grid two" style="margin-top:18px">
   ${
    ins.map(i=>`
     <div class="card">
      <span class="pill ${i.priority==="High"?"danger":"warn"}">${i.priority} priority</span>
      <div class="insight ${i.priority.toLowerCase()}">
       <h3>${i.title}</h3>
       <p>${i.detail}</p>
       <p><b>Recommended action:</b> ${i.action}</p>
      </div>
     </div>
    `).join("")
   }
  </div>
 `)+
 `
 <div class="card" style="margin-top:18px">
  <div class="section-title">Decision workflow</div>
  <div class="grid three">
   <div><b>1. Measure</b><p class="note">Track the business KPI.</p></div>
   <div><b>2. Explain</b><p class="note">${hasAdvancedAccess()?"Use product, customer and funnel patterns to explain the KPI.":"Basic analysis shows the KPI; advanced plans explain the pattern behind it."}</p></div>
   <div><b>3. Decide</b><p class="note">${hasAdvancedAccess()?"Prioritize a recommended action using evidence.":"Upgrade to unlock recommendation-driven decision support."}</p></div>
  </div>
 </div>
 `;
}

async function subscriptionPage(){

 shell("subscription");

 const res=await api("/subscription/plans");
 const plans=res.plans;

 document.getElementById("content").innerHTML=
 header("Plans & Billing","Start with basic analysis and upgrade when your business needs deeper decision intelligence.")+
 `
 <div class="billing-hero">
  <div>
   <span class="eyebrow">Ecomlytics subscription</span>
   <h2>${hasAdvancedAccess()?`You're on the ${planMeta().name} plan.`:"You're currently on the Free plan."}</h2>
   <p>${hasAdvancedAccess()?"Advanced analytics are enabled for this workspace.":"Basic analysis remains available at no cost. Upgrade when you need advanced insights, recommendations and decision intelligence."}</p>
  </div>
  <div class="billing-status"><span class="status-dot"></span>${hasAdvancedAccess()?"Advanced access enabled":"Basic access"}</div>
 </div>

 <div class="card" style="margin-top:18px">
  <div class="section-title">Choose your level</div>
  <p class="note">The subscription structure follows the Ecomlytics product plan: Free ₹0, Starter ₹999/month, Growth ₹2,999/month and Pro ₹7,999/month.</p>
 </div>

 <div class="pricing-grid" style="margin-top:18px">
  ${plans.map(p=>`
   <div class="pricing-card ${p.id===currentPlan()?"current":""} ${p.id==="growth"?"featured":""}">
    ${p.id==="growth"?`<div class="featured-label">Recommended for growing teams</div>`:""}
    <div class="pricing-top">
     <div><div class="plan-name">${p.name}</div><p>${p.description}</p></div>
     ${p.id===currentPlan()?`<span class="pill good">Current plan</span>`:""}
    </div>
    <div class="price">${p.price===0?"₹0":"₹"+fmt(p.price)}<small>${p.price===0?"forever":"/ month"}</small></div>
    <div class="pricing-divider"></div>
    <ul class="feature-list">${p.features.map(f=>`<li><span>✓</span>${f}</li>`).join("")}</ul>
    ${p.id==="free"
      ? `<button class="btn secondary-btn" disabled>Basic analysis</button>`
      : p.id===currentPlan()
      ? `<button class="btn secondary-btn" disabled>Active plan</button>`
      : `<button class="btn" onclick="openPayment('${p.id}')">Upgrade to ${p.name}</button>`}
   </div>
  `).join("")}
 </div>

 <div class="card" style="margin-top:18px">
  <div class="section-title">How Ecomlytics grows with you</div>
  <div class="grid four">
   <div><span class="step-num">01</span><b>Measure</b><p class="note">Basic sales, product, customer and funnel metrics.</p></div>
   <div><span class="step-num">02</span><b>Understand</b><p class="note">Advanced patterns and performance analysis on paid plans.</p></div>
   <div><span class="step-num">03</span><b>Explain</b><p class="note">The insight engine turns patterns into business explanations.</p></div>
   <div><span class="step-num">04</span><b>Decide</b><p class="note">Recommendations and future AI Advisor capabilities.</p></div>
  </div>
 </div>

 <div class="card" style="margin-top:18px">
  <div class="section-title">Payment history</div>
  <div id="paymentHistory" class="payment-history"></div>
 </div>

 <div id="paymentModal" class="modal-backdrop" style="display:none">
  <div class="payment-modal">
   <button class="modal-close" onclick="closePayment()">×</button>
   <div class="eyebrow">Demo checkout</div>
   <h2 id="paymentTitle">Upgrade</h2>
   <p class="note">Duplicate/demo payment flow for the project. It does not charge real money or connect to a payment gateway.</p>
   <form id="paymentForm">
    <input type="hidden" id="payPlan">
    <div class="field"><label>Cardholder name</label><input id="cardName" class="input" placeholder="Alex Johnson" required></div>
    <div class="field"><label>Card number</label><input id="cardNumber" class="input" inputmode="numeric" maxlength="19" placeholder="4242 4242 4242 4242" required></div>
    <div class="grid two">
     <div class="field"><label>Expiry</label><input id="cardExpiry" class="input" placeholder="12/29" required></div>
     <div class="field"><label>CVV</label><input id="cardCvv" class="input" maxlength="4" placeholder="123" required></div>
    </div>
    <div id="paymentError" class="error"></div>
    <button class="btn login-btn" type="submit">Pay & activate plan</button>
   </form>
   <div id="paymentSuccess" class="payment-success" style="display:none"></div>
  </div>
 </div>
 `;

 renderPaymentHistory();
 document.getElementById("paymentForm").addEventListener("submit",processPayment);
}

function openPayment(plan){
 const p=PLAN_META[plan];
 if(!p || !p.price) return;
 document.getElementById("payPlan").value=plan;
 document.getElementById("paymentTitle").textContent=`Upgrade to ${p.name} · ₹${fmt(p.price)}/month`;
 document.getElementById("paymentError").style.display="none";
 document.getElementById("paymentForm").style.display="block";
 document.getElementById("paymentSuccess").style.display="none";
 document.getElementById("paymentModal").style.display="flex";
}
function closePayment(){ const m=document.getElementById("paymentModal"); if(m)m.style.display="none"; }

async function processPayment(e){
 e.preventDefault();
 const plan=document.getElementById("payPlan").value;
 const err=document.getElementById("paymentError");
 const card=document.getElementById("cardNumber").value.replace(/\s/g,"");
 if(card.length<12){err.textContent="Enter a valid demo card number.";err.style.display="block";return;}
 try{
  const r=await fetch(API+"/subscription/checkout",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({plan,card_last4:card.slice(-4)})});
  const data=await r.json();
  if(!r.ok) throw new Error(data.detail||"Payment failed");
  localStorage.setItem("ecomlytics_plan",plan);
  const history=JSON.parse(localStorage.getItem("ecomlytics_payments")||"[]");
  history.unshift({transaction_id:data.transaction_id,plan:data.plan.name,amount:data.plan.price,date:new Date().toISOString(),mode:"Demo"});
  localStorage.setItem("ecomlytics_payments",JSON.stringify(history.slice(0,10)));
  document.getElementById("paymentForm").style.display="none";
  document.getElementById("paymentSuccess").style.display="block";
  document.getElementById("paymentSuccess").innerHTML=`<div class="success-icon">✓</div><h3>Payment approved</h3><p>${data.message}</p><p class="note">Transaction: <b>${data.transaction_id}</b></p><button class="btn" onclick="window.location.reload()">Continue to Ecomlytics</button>`;
 }catch(ex){err.textContent=ex.message||"Could not complete the demo payment.";err.style.display="block";}
}

function renderPaymentHistory(){
 const el=document.getElementById("paymentHistory"); if(!el)return;
 const history=JSON.parse(localStorage.getItem("ecomlytics_payments")||"[]");
 if(!history.length){el.innerHTML='<div class="empty">No payments yet. Your demo transactions will appear here.</div>';return;}
 el.innerHTML=`<div class="table-wrap"><table class="table"><thead><tr><th>Transaction</th><th>Plan</th><th>Amount</th><th>Date</th><th>Mode</th></tr></thead><tbody>${history.map(x=>`<tr><td><b>${x.transaction_id}</b></td><td>${x.plan}</td><td>${money(x.amount)}</td><td>${new Date(x.date).toLocaleString()}</td><td><span class="pill">Demo</span></td></tr>`).join("")}</tbody></table></div>`;
}

async function dataSourcesPage(){

 shell("data-sources");

 const res = await api("/data-sources");
 const sources = res.sources;

 const stateBadge = s => {
  const map = {
   connected: ["Connected","ok"],
   disconnected: ["Not connected","warn"],
   not_configured: ["Configuration required","warn"],
   syncing: ["Syncing","info"],
  };
  const [label, cls] = map[s] || [s, "warn"];
  return `<span class="source-state ${cls}">${label}</span>`;
 };

 document.getElementById("content").innerHTML =

 header(
  "Data Sources",
  "Connect and manage where your analytics data comes from"
 ) +

 `<div class="grid two" style="margin-top:18px">` +

 sources.map(s => `
  <div class="card">
   <div class="section-title">${s.name}</div>
   ${stateBadge(s.state)}
   <p class="note" style="margin-top:8px">${s.message || ""}</p>
   ${s.property_id ? `<p class="note">Property: ${s.property_id}</p>` : ""}
   <p class="note">Last synced: ${s.last_synced ? new Date(s.last_synced).toLocaleString() : "Never"}</p>
   ${s.id === "google_analytics" ? `<button class="btn" id="connect-ga">Connect Google Analytics</button>` : ""}
  </div>
 `).join("") +

 `</div>`;

 const btn = document.getElementById("connect-ga");
 if(btn){
  btn.onclick = async () => {
   try {
    const r = await fetch(API + "/data-sources/google/connect", {method:"POST"});
    const data = await r.json();
    if(!r.ok){
     alert(data.detail || "Google Analytics is not configured on this server yet.");
     return;
    }
    window.location.href = data.authorization_url;
   } catch(e){
    alert("Could not start the Google Analytics connection.");
   }
  };
 }
}

const page=document.body.dataset.page;

if(page==="overview") overviewPage();

if(page==="data-sources") dataSourcesPage();

if(page==="sales") salesPage();

if(page==="products") productsPage();

if(page==="customers") customersPage();

if(page==="retention") retentionPage();

if(page==="insights") insightsPage();

if(page==="subscription") subscriptionPage();