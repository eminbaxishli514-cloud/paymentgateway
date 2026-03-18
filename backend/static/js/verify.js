/**
 * SMS verification page. Completes pending card payments.
 */

(function () {
  "use strict";

  const params = new URLSearchParams(window.location.search);
  const paymentId = params.get("payment_id");
  const form = document.getElementById("verifyForm");
  const codeInput = document.getElementById("smsCode");
  const verifyBtn = document.getElementById("verifyBtn");

  if (!paymentId) {
    document.querySelector(".verify-card").innerHTML =
      '<div class="result-card error"><h3>Missing payment</h3><p>No payment ID provided. <a href="/">Return to checkout</a>.</p></div>';
    return;
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    const code = codeInput.value.trim();
    if (!code) return;

    verifyBtn.classList.add("loading");
    verifyBtn.disabled = true;
    document.getElementById("codeError").textContent = "";

    try {
      const res = await fetch("/api/payments/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ payment_id: paymentId, code: code }),
      });
      const data = await res.json();

      if (data.success) {
        window.location.href = "/receipt?payment_id=" + encodeURIComponent(paymentId);
      } else {
        document.getElementById("codeError").textContent = data.message || "Invalid code";
        verifyBtn.classList.remove("loading");
        verifyBtn.disabled = false;
      }
    } catch {
      document.getElementById("codeError").textContent = "Connection error. Please try again.";
      verifyBtn.classList.remove("loading");
      verifyBtn.disabled = false;
    }
  });

})();
