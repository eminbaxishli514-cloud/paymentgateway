/**
 * Admin SIEM dashboard — uses X-Admin-Token from sessionStorage.
 */
(function () {
  "use strict";

  const TOKEN_KEY = "admin_api_token";

  function getToken() {
    return sessionStorage.getItem(TOKEN_KEY) || "";
  }

  function setError(msg) {
    const el = document.getElementById("adminError");
    el.textContent = msg || "";
  }

  async function api(path, options = {}) {
    const token = getToken();
    const headers = {
      "Content-Type": "application/json",
      ...options.headers,
    };
    if (token) headers["X-Admin-Token"] = token;
    const res = await fetch(path, { ...options, headers });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || res.statusText || "Request failed");
    }
    return data;
  }

  function fmtTime(ts) {
    return new Date(ts * 1000).toLocaleString();
  }

  async function loadDashboard() {
    setError("");
    const data = await api("/api/admin/siem/dashboard");
    const stats = document.getElementById("summaryStats");
    stats.innerHTML = `
      <div class="admin-stat"><strong>${data.total_events_buffered}</strong><span>Events buffered</span></div>
      <div class="admin-stat"><strong>${data.unique_ips_recent}</strong><span>IPs (5 min)</span></div>
      <div class="admin-stat"><strong>${data.suspicious_ip_count}</strong><span>Suspicious IPs</span></div>
      <div class="admin-stat"><strong>${data.blocked_ips.length}</strong><span>Blocked</span></div>
    `;

    const tbody = document.querySelector("#ipTable tbody");
    tbody.innerHTML = "";
    (data.top_ips || []).forEach((row) => {
      const tr = document.createElement("tr");
      if (row.suspicious) tr.classList.add("row-suspicious");
      tr.innerHTML = `
        <td><code>${escapeHtml(row.ip)}</code></td>
        <td>${row.requests_last_60s}</td>
        <td>${row.requests_last_5m}</td>
        <td><code>${escapeHtml(row.last_path || "")}</code></td>
        <td>${row.suspicious ? escapeHtml(row.reason || "Suspicious") : "—"}</td>
        <td><button type="button" class="btn-block" data-ip="${escapeHtml(row.ip)}">Block</button></td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll(".btn-block").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const ip = btn.getAttribute("data-ip");
        if (!ip || !confirm(`Block ${ip}?`)) return;
        try {
          await api("/api/admin/siem/block", { method: "POST", body: JSON.stringify({ ip }) });
          await loadDashboard();
          await loadBlocked();
        } catch (e) {
          setError(e.message);
        }
      });
    });

    await loadBlocked();
    await loadEvents();
  }

  async function loadBlocked() {
    const data = await api("/api/admin/siem/blocked");
    const ul = document.getElementById("blockedList");
    ul.innerHTML = "";
    if (!data.blocked_ips.length) {
      ul.innerHTML = "<li>None</li>";
      return;
    }
    data.blocked_ips.forEach((ip) => {
      const li = document.createElement("li");
      li.innerHTML = `<span>${escapeHtml(ip)}</span><button type="button" class="btn-unblock" data-ip="${escapeHtml(ip)}">Unblock</button>`;
      ul.appendChild(li);
    });
    ul.querySelectorAll(".btn-unblock").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const ip = btn.getAttribute("data-ip");
        try {
          await api("/api/admin/siem/unblock", { method: "POST", body: JSON.stringify({ ip }) });
          await loadDashboard();
          await loadBlocked();
        } catch (e) {
          setError(e.message);
        }
      });
    });
  }

  async function loadEvents() {
    const data = await api("/api/admin/siem/events?limit=80");
    const tbody = document.querySelector("#eventsTable tbody");
    tbody.innerHTML = "";
    (data.events || []).forEach((e) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${fmtTime(e.ts)}</td>
        <td><code>${escapeHtml(e.ip)}</code></td>
        <td>${escapeHtml(e.method)}</td>
        <td><code>${escapeHtml(e.path)}</code></td>
        <td>${e.status_code}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  document.getElementById("saveToken").addEventListener("click", async () => {
    const v = document.getElementById("adminToken").value.trim();
    if (!v) {
      setError("Enter admin token");
      return;
    }
    sessionStorage.setItem(TOKEN_KEY, v);
    try {
      await loadDashboard();
      document.getElementById("authCard").classList.add("hidden");
      document.getElementById("dashboard").classList.remove("hidden");
      setError("");
    } catch (e) {
      sessionStorage.removeItem(TOKEN_KEY);
      setError(e.message);
    }
  });

  document.getElementById("refreshEvents").addEventListener("click", () => {
    loadEvents().catch((e) => setError(e.message));
  });

  if (getToken()) {
    document.getElementById("adminToken").value = "••••••••";
    loadDashboard()
      .then(() => {
        document.getElementById("authCard").classList.add("hidden");
        document.getElementById("dashboard").classList.remove("hidden");
      })
      .catch(() => {
        sessionStorage.removeItem(TOKEN_KEY);
      });
  }
})();
