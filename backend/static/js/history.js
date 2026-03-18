/**
 * Transaction history page.
 */

(function () {
  "use strict";

  const listEl = document.getElementById("historyList");
  const emptyEl = document.getElementById("historyEmpty");
  const loadingEl = document.getElementById("historyLoading");

  async function loadHistory() {
    try {
      const res = await fetch("/api/payments/history");
      const data = await res.json();
      const txns = data.transactions || [];

      loadingEl.classList.add("hidden");

      if (txns.length === 0) {
        emptyEl.classList.remove("hidden");
        return;
      }

      emptyEl.classList.add("hidden");
      const fmt = (n, c) =>
        new Intl.NumberFormat("en-US", { style: "currency", currency: c || "USD" }).format(n);

      listEl.innerHTML = txns
        .map((t) => {
          const date = new Date(t.created_at).toLocaleString("en-US", {
            dateStyle: "short",
            timeStyle: "short",
          });
          const statusClass =
            t.status === "succeeded"
              ? "success"
              : t.status === "failed"
                ? "error"
                : t.status === "refunded"
                  ? "refunded"
                  : "pending";
          const method = (t.payment_method || "card").replace("_", " ");
          const cardInfo = t.card_last_four ? ` •••• ${t.card_last_four}` : "";
          const receiptLink =
            t.status === "succeeded" || t.status === "refunded"
              ? `<a href="/receipt?payment_id=${encodeURIComponent(t.id)}" class="txn-link">Receipt</a>`
              : "";

          return `
          <div class="history-item ${statusClass}">
            <div class="txn-main">
              <span class="txn-id">${t.id}</span>
              <span class="txn-status">${t.status}</span>
            </div>
            <div class="txn-details">
              <span class="txn-amount">${fmt(t.total || t.amount, t.currency)}</span>
              <span class="txn-meta">${method}${cardInfo} • ${date}</span>
            </div>
            <div class="txn-actions">${receiptLink}</div>
          </div>
        `;
        })
        .join("");
    } catch {
      loadingEl.classList.add("hidden");
      emptyEl.classList.remove("hidden");
      emptyEl.innerHTML = "<p>Could not load history.</p>";
    }
  }

  loadHistory();
})();
