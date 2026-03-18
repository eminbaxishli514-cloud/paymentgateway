/**
 * Payment form handling and API integration.
 * Supports multiple payment methods, saved cards, and SMS verification flow.
 */

(function () {
  "use strict";

  const form = document.getElementById("paymentForm");
  const submitBtn = document.getElementById("submitBtn");
  const amountInput = document.getElementById("amount");
  const cardNumberInput = document.getElementById("cardNumber");
  const savedCardSelect = document.getElementById("savedCard");
  const resultCard = document.getElementById("result");

  // Pre-fill from sessionStorage (store checkout) or URL params (fallback)
  (function initCheckoutData() {
    let amount = sessionStorage.getItem("checkout_amount");
    let description = sessionStorage.getItem("checkout_description");
    if (!amount || !description) {
      const params = new URLSearchParams(window.location.search);
      amount = amount || params.get("amount");
      description = description || params.get("description");
    }
    if (amount) {
      const num = parseFloat(amount);
      if (!isNaN(num) && num > 0) {
        amountInput.value = num.toFixed(2);
      }
    }
    if (description) {
      const descEl = document.getElementById("orderDescription");
      if (descEl) descEl.textContent = description;
    }
    if (window.location.search) {
      history.replaceState({}, "", window.location.pathname);
    }
  })();

  // Format card number with spaces
  if (cardNumberInput) {
    cardNumberInput.addEventListener("input", function () {
      let value = this.value.replace(/\D/g, "");
      value = value.replace(/(\d{4})(?=\d)/g, "$1 ");
      this.value = value;
    });
  }

  // Update displayed amount
  function updateAmounts() {
    if (!amountInput) return;
    const val = parseFloat(amountInput.value) || 0;
    const fmt = (n) =>
      new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);
    document.getElementById("displayAmount").textContent = fmt(val);
    document.getElementById("displayTotal").textContent = fmt(val);
  }

  if (amountInput) amountInput.addEventListener("input", updateAmounts);

  // Payment method toggle
  const methodRadios = document.querySelectorAll('input[name="payment_method"]');
  const cardSection = document.getElementById("cardSection");
  const newCardFields = document.getElementById("newCardFields");

  function toggleCardSection() {
    const method = document.querySelector('input[name="payment_method"]:checked').value;
    cardSection.classList.toggle("hidden", method !== "card");
    updateSubmitButtonText();
  }

  function updateSubmitButtonText() {
    const method = document.querySelector('input[name="payment_method"]:checked').value;
    const btnText = submitBtn.querySelector(".btn-text");
    if (!btnText) return;
    if (method === "paypal") btnText.textContent = "Pay with PayPal";
    else if (method === "apple_pay") btnText.textContent = "Pay with Apple Pay";
    else btnText.textContent = "Pay";
  }

  methodRadios.forEach((r) => {
    r.addEventListener("change", toggleCardSection);
    r.addEventListener("click", toggleCardSection);
  });

  // Saved card toggle
  savedCardSelect.addEventListener("change", function () {
    if (this.value) {
      newCardFields.classList.add("hidden");
    } else {
      newCardFields.classList.remove("hidden");
    }
    validateForm();
  });

  // Format expiry
  const expMonth = document.getElementById("expMonth");
  if (expMonth) {
    expMonth.addEventListener("input", function () {
      if (this.value.length === 2) document.getElementById("expYear").focus();
    });
  }

  // Validate and enable submit
  form.addEventListener("input", debounce(validateForm, 300));
  form.addEventListener("change", validateForm);

  function validateForm() {
    if (!amountInput) return;
    const method = document.querySelector('input[name="payment_method"]:checked').value;
    const amount = parseFloat(amountInput.value) || 0;
    let valid = amount > 0;

    if (method === "card") {
      const saved = savedCardSelect.value;
      if (saved) {
        valid = valid && true;
      } else {
        const month = parseInt(expMonth.value, 10);
        const year = parseInt(document.getElementById("expYear").value, 10);
        valid =
          valid &&
          document.getElementById("cardholder").value.trim().length >= 2 &&
          cardNumberInput.value.replace(/\s/g, "").length >= 13 &&
          month >= 1 && month <= 12 &&
          year >= 24 && year <= 30 &&
          document.getElementById("cvc").value.length >= 3;
      }
    }

    submitBtn.disabled = !valid;
    clearErrors();
  }

  function clearErrors() {
    document.querySelectorAll(".field-error").forEach((el) => (el.textContent = ""));
  }

  function showResult(success, title, message, paymentId) {
    resultCard.classList.remove("hidden", "success", "error");
    resultCard.classList.add(success ? "success" : "error");
    document.getElementById("resultIcon").textContent = success ? "✓" : "✕";
    document.getElementById("resultTitle").textContent = title;
    document.getElementById("resultMessage").textContent = message;
    document.getElementById("resultId").textContent = paymentId ? `ID: ${paymentId}` : "";
    resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    if (submitBtn.disabled) return;

    submitBtn.classList.add("loading");
    submitBtn.disabled = true;
    clearErrors();

    const method = document.querySelector('input[name="payment_method"]:checked').value;
    const savedCard = savedCardSelect.value;

    const descEl = document.getElementById("orderDescription");
    const description = descEl && descEl.textContent !== "Demo product" ? descEl.textContent : null;

    const payload = {
      amount: parseFloat(amountInput.value),
      currency: "USD",
      payment_method: method,
      saved_card_id: savedCard || null,
      description: description,
    };

    if (method === "card" && !savedCard) {
      payload.card_number = cardNumberInput.value.replace(/\s/g, "");
      payload.card_exp_month = parseInt(expMonth.value, 10);
      payload.card_exp_year = 2000 + parseInt(document.getElementById("expYear").value, 10);
      payload.card_cvc = document.getElementById("cvc").value;
      payload.cardholder_name = document.getElementById("cardholder").value.trim();
    }

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

      if (data.requires_verification) {
        sessionStorage.removeItem("checkout_amount");
        sessionStorage.removeItem("checkout_description");
        window.location.href = "/verify?payment_id=" + encodeURIComponent(data.id);
        return;
      }

      if (data.status === "succeeded") {
        sessionStorage.removeItem("checkout_amount");
        sessionStorage.removeItem("checkout_description");
        window.location.href = "/receipt?payment_id=" + encodeURIComponent(data.id);
        return;
      }

      showResult(
        false,
        "Payment declined",
        data.failure_reason || "Your card was declined.",
        data.id
      );
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

  toggleCardSection();
  updateAmounts();
  validateForm();
})();
