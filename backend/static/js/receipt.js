/**
 * Receipt page. Displays payment details and allows download.
 */

(function () {
  "use strict";

  const params = new URLSearchParams(window.location.search);
  const paymentId = params.get("payment_id");
  const receiptCard = document.getElementById("receiptCard");
  const receiptError = document.getElementById("receiptError");
  const receiptLoading = document.getElementById("receiptLoading");

  async function loadReceipt() {
    if (!paymentId) {
      showError();
      return;
    }
    try {
      const res = await fetch("/api/payments/receipt/" + encodeURIComponent(paymentId));
      if (!res.ok) {
        showError();
        return;
      }
      const data = await res.json();
      renderReceipt(data);
    } catch {
      showError();
    }
  }

  function showError() {
    receiptLoading.classList.add("hidden");
    receiptError.classList.remove("hidden");
  }

  function renderReceipt(data) {
    receiptLoading.classList.add("hidden");
    receiptCard.classList.remove("hidden");

    const fmt = (n) =>
      new Intl.NumberFormat("en-US", { style: "currency", currency: data.currency || "USD" }).format(n);
    const date = new Date(data.created_at);
    const dateStr = date.toLocaleString("en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    });

    document.getElementById("receiptId").textContent = data.id;
    document.getElementById("receiptDate").textContent = dateStr;
    document.getElementById("receiptAmount").textContent = fmt(data.amount);

    const discountRow = document.getElementById("receiptDiscountRow");
    const cardRow = document.getElementById("receiptCardRow");
    if (data.discount > 0) {
      discountRow.classList.remove("hidden");
      document.getElementById("receiptDiscount").textContent = "-" + fmt(data.discount);
    } else {
      discountRow.classList.add("hidden");
    }

    document.getElementById("receiptTotal").textContent = fmt(data.total || data.amount);

    const method = (data.payment_method || "card").replace("_", " ");
    document.getElementById("receiptMethod").textContent =
      method.charAt(0).toUpperCase() + method.slice(1);

    if (data.card_last_four) {
      cardRow.classList.remove("hidden");
      document.getElementById("receiptCard").textContent = "•••• " + data.card_last_four;
    } else {
      cardRow.classList.add("hidden");
    }
  }

  document.getElementById("downloadReceipt").addEventListener("click", function () {
    const data = {
      id: document.getElementById("receiptId").textContent,
      date: document.getElementById("receiptDate").textContent,
      amount: document.getElementById("receiptAmount").textContent,
      total: document.getElementById("receiptTotal").textContent,
      method: document.getElementById("receiptMethod").textContent,
    };
    const text = [
      "PAYFLOW RECEIPT",
      "==================",
      "Payment ID: " + data.id,
      "Date: " + data.date,
      "Amount: " + data.amount,
      "Total paid: " + data.total,
      "Method: " + data.method,
      "",
      "Thank you for your payment.",
    ].join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "receipt-" + data.id + ".txt";
    a.click();
    URL.revokeObjectURL(url);
  });

  loadReceipt();
})();
