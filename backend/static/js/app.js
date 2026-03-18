/**
 * Payment form handling and API integration.
 * Supports multiple payment methods, saved cards, promo codes, and SMS verification flow.
 */

(function () {
  "use strict";

  const form = document.getElementById("paymentForm");
  const submitBtn = document.getElementById("submitBtn");
  const amountInput = document.getElementById("amount");
  const cardNumberInput = document.getElementById("cardNumber");
  const savedCardSelect = document.getElementById("savedCard");
  const promoInput = document.getElementById("promoCode");
  const applyPromoBtn = document.getElementById("applyPromo");
  const resultCard = document.getElementById("result");

  let appliedPromo = null; // { percent, description }

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
    const val = parseFloat(amountInput.value) || 0;
    const pct = appliedPromo ? appliedPromo.percent : 0;
    const discount = val * (pct / 100);
    const total = val - discount;

    const fmt = (n) =>
      new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);

    document.getElementById("displayAmount").textContent = fmt(val);
    document.getElementById("displayDiscount").textContent = discount > 0 ? "-" + fmt(discount) : "$0.00";
    document.getElementById("displayTotal").textContent = fmt(total);

    const promoRow = document.getElementById("promoRow");
    const promoLabel = document.getElementById("promoLabel");
    if (appliedPromo) {
      promoRow.classList.remove("hidden");
      promoLabel.textContent = "(" + appliedPromo.description + ")";
    } else {
      promoRow.classList.add("hidden");
    }
  }

  amountInput.addEventListener("input", updateAmounts);

  // Apply promo code
  applyPromoBtn.addEventListener("click", async function () {
    const code = promoInput.value.trim();
    document.getElementById("promoError").textContent = "";
    if (!code) {
      appliedPromo = null;
      updateAmounts();
      return;
    }
    try {
      const res = await fetch("/api/payments/promo/" + encodeURIComponent(code));
      const data = await res.json();
      if (data.valid && data.percent) {
        appliedPromo = { percent: data.percent, description: data.description || data.percent + "% off" };
        promoInput.classList.add("promo-applied");
        document.getElementById("promoError").textContent = "";
      } else {
        appliedPromo = null;
        promoInput.classList.remove("promo-applied");
        document.getElementById("promoError").textContent = data.message || "Invalid code";
      }
    } catch {
      appliedPromo = null;
      document.getElementById("promoError").textContent = "Could not validate code";
    }
    updateAmounts();
  });

  // Payment method toggle
  const methodRadios = document.querySelectorAll('input[name="payment_method"]');
  const cardSection = document.getElementById("cardSection");
  const newCardFields = document.getElementById("newCardFields");

  function toggleCardSection() {
    const method = document.querySelector('input[name="payment_method"]:checked').value;
    if (method === "card") {
      cardSection.classList.remove("hidden");
    } else {
      cardSection.classList.add("hidden");
    }
  }

  methodRadios.forEach((r) => r.addEventListener("change", toggleCardSection));

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
    const method = document.querySelector('input[name="payment_method"]:checked').value;
    let valid = amountInput.validity.valid && amountInput.value && parseFloat(amountInput.value) > 0;

    if (method === "card") {
      const saved = savedCardSelect.value;
      if (saved) {
        valid = valid && true;
      } else {
        valid =
          valid &&
          document.getElementById("cardholder").value.trim().length >= 2 &&
          cardNumberInput.value.replace(/\s/g, "").length >= 13 &&
          expMonth.validity.valid &&
          document.getElementById("expYear").validity.valid &&
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

    const payload = {
      amount: parseFloat(amountInput.value),
      currency: "USD",
      payment_method: method,
      saved_card_id: savedCard || null,
      description: document.getElementById("description").value.trim() || null,
      promo_code: promoInput.value.trim() || null,
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
        window.location.href = "/verify?payment_id=" + encodeURIComponent(data.id);
        return;
      }

      if (data.status === "succeeded") {
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
