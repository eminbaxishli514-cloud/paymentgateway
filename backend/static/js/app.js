/**
 * Payment form handling and API integration.
 * Keeps logic simple and readable.
 */

(function () {
  "use strict";

  const form = document.getElementById("paymentForm");
  const submitBtn = document.getElementById("submitBtn");
  const amountInput = document.getElementById("amount");
  const cardNumberInput = document.getElementById("cardNumber");
  const resultCard = document.getElementById("result");

  // Format card number with spaces
  cardNumberInput.addEventListener("input", function () {
    let value = this.value.replace(/\D/g, "");
    value = value.replace(/(\d{4})(?=\d)/g, "$1 ");
    this.value = value;
  });

  // Update displayed amount
  amountInput.addEventListener("input", function () {
    const val = parseFloat(this.value) || 0;
    const formatted = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(val);
    document.getElementById("displayAmount").textContent = formatted;
    document.getElementById("displayTotal").textContent = formatted;
  });

  // Format expiry inputs
  document.getElementById("expMonth").addEventListener("input", function () {
    if (this.value.length === 2) document.getElementById("expYear").focus();
  });

  // Validate and enable submit when form is valid
  form.addEventListener("input", debounce(validateForm, 300));
  form.addEventListener("change", validateForm);

  function validateForm() {
    const valid =
      amountInput.validity.valid &&
      amountInput.value &&
      parseFloat(amountInput.value) > 0 &&
      document.getElementById("cardholder").value.trim().length >= 2 &&
      cardNumberInput.value.replace(/\s/g, "").length >= 13 &&
      document.getElementById("expMonth").validity.valid &&
      document.getElementById("expYear").validity.valid &&
      document.getElementById("cvc").value.length >= 3;

    submitBtn.disabled = !valid;
    clearErrors();
  }

  function clearErrors() {
    document.querySelectorAll(".field-error").forEach((el) => (el.textContent = ""));
  }

  function showError(fieldId, message) {
    const el = document.getElementById(fieldId + "Error");
    if (el) el.textContent = message;
  }

  function showResult(success, title, message, paymentId) {
    resultCard.classList.remove("hidden", "success", "error");
    resultCard.classList.add(success ? "success" : "error");
    document.getElementById("resultIcon").textContent = success ? "✓" : "✕";
    document.getElementById("resultTitle").textContent = title;
    document.getElementById("resultMessage").textContent = message;
    document.getElementById("resultId").textContent = paymentId
      ? `ID: ${paymentId}`
      : "";
    resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    if (submitBtn.disabled) return;

    submitBtn.classList.add("loading");
    submitBtn.disabled = true;
    clearErrors();

    const payload = {
      amount: parseFloat(amountInput.value),
      currency: "USD",
      card_number: cardNumberInput.value.replace(/\s/g, ""),
      card_exp_month: parseInt(document.getElementById("expMonth").value, 10),
      card_exp_year: 2000 + parseInt(document.getElementById("expYear").value, 10),
      card_cvc: document.getElementById("cvc").value,
      cardholder_name: document.getElementById("cardholder").value.trim(),
      description: document.getElementById("description").value.trim() || null,
    };

    try {
      const res = await fetch("/api/payments/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        const msg = data.detail || "Payment failed";
        const errMsg = Array.isArray(msg) ? msg.map((x) => x.msg).join(" ") : msg;
        showResult(false, "Payment failed", errMsg, null);
        return;
      }

      if (data.status === "succeeded") {
        showResult(
          true,
          "Payment successful",
          `Your payment of $${data.amount.toFixed(2)} has been processed.`,
          data.id
        );
      } else {
        showResult(
          false,
          "Payment declined",
          data.failure_reason || "Your card was declined.",
          data.id
        );
      }
    } catch (err) {
      showResult(
        false,
        "Connection error",
        "Could not reach the server. Please try again.",
        null
      );
    } finally {
      submitBtn.classList.remove("loading");
      validateForm();
    }
  });

  function debounce(fn, ms) {
    let t;
    return function () {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(this, arguments), ms);
    };
  }

  // Initial validation
  validateForm();
})();
