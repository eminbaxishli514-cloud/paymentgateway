/**
 * MarketPlace - Cart logic and purchase flow.
 * Adds items to cart, manages quantities, and redirects to payment gateway on Purchase.
 */

(function () {
  "use strict";

  const CART_KEY = "marketplace_cart";
  const PRODUCT_ICONS = {
    phone: "📱",
    water: "💧",
    laptop: "💻",
    headphones: "🎧",
    watch: "⌚",
    tablet: "📱",
  };

  let cart = loadCart();

  function loadCart() {
    try {
      const raw = localStorage.getItem(CART_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  function saveCart() {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    renderCart();
    updateCartCount();
  }

  function updateCartCount() {
    const countEl = document.getElementById("cartCount");
    if (!countEl) return;
    const total = cart.reduce((sum, item) => sum + item.qty, 0);
    countEl.textContent = total;
    countEl.setAttribute("data-count", total);
    if (total > 0) {
      countEl.style.display = "flex";
    } else {
      countEl.style.display = "none";
    }
  }

  function addToCart(id, name, price) {
    const numPrice = parseFloat(price);
    const existing = cart.find((item) => item.id === id);
    if (existing) {
      existing.qty += 1;
    } else {
      cart.push({ id, name, price: numPrice, qty: 1 });
    }
    saveCart();
    flashAddButton(id);
  }

  function removeFromCart(id) {
    cart = cart.filter((item) => item.id !== id);
    saveCart();
  }

  function updateQty(id, delta) {
    const item = cart.find((item) => item.id === id);
    if (!item) return;
    item.qty += delta;
    if (item.qty <= 0) {
      removeFromCart(id);
    } else {
      saveCart();
    }
  }

  function flashAddButton(id) {
    const btn = document.querySelector(`.btn-add[data-id="${id}"]`);
    if (btn) {
      btn.classList.add("added");
      btn.textContent = "Added!";
      setTimeout(() => {
        btn.classList.remove("added");
        btn.textContent = "Add to cart";
      }, 800);
    }
  }

  function getTotal() {
    return cart.reduce((sum, item) => sum + item.price * item.qty, 0);
  }

  function getDescription() {
    return cart.map((item) => `${item.name} x${item.qty}`).join(", ");
  }

  function renderCart() {
    const container = document.getElementById("cartItems");
    const emptyEl = document.getElementById("cartEmpty");
    const footer = document.getElementById("cartFooter");
    const purchaseBtn = document.getElementById("purchaseBtn");

    if (!container) return;

    if (cart.length === 0) {
      emptyEl.style.display = "";
      container.querySelectorAll(".cart-item").forEach((el) => el.remove());
      footer.style.display = "none";
      purchaseBtn.classList.add("btn-purchase-disabled");
      return;
    }

    emptyEl.style.display = "none";
    footer.style.display = "";
    purchaseBtn.classList.remove("btn-purchase-disabled");

    const existingItems = container.querySelectorAll(".cart-item");
    existingItems.forEach((el) => el.remove());

    cart.forEach((item) => {
      const icon = PRODUCT_ICONS[item.id] || "📦";
      const subtotal = (item.price * item.qty).toFixed(2);
      const div = document.createElement("div");
      div.className = "cart-item";
      div.innerHTML = `
        <div class="cart-item-image">${icon}</div>
        <div class="cart-item-details">
          <p class="cart-item-name">${escapeHtml(item.name)}</p>
          <p class="cart-item-qty">Qty: ${item.qty} × $${item.price.toFixed(2)}</p>
        </div>
        <div class="cart-item-price">$${subtotal}</div>
        <div class="cart-item-actions">
          <button type="button" class="cart-item-btn" data-action="minus" data-id="${escapeHtml(item.id)}" aria-label="Decrease">−</button>
          <span class="cart-item-qty-display">${item.qty}</span>
          <button type="button" class="cart-item-btn" data-action="plus" data-id="${escapeHtml(item.id)}" aria-label="Increase">+</button>
          <button type="button" class="cart-item-btn remove" data-action="remove" data-id="${escapeHtml(item.id)}" aria-label="Remove">×</button>
        </div>
      `;
      container.appendChild(div);
    });

    const total = getTotal();
    document.getElementById("cartTotalAmount").textContent =
      new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(total);

    const checkoutUrl = buildCheckoutUrl();
    purchaseBtn.href = checkoutUrl;

    container.querySelectorAll(".cart-item-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        const action = this.getAttribute("data-action");
        const id = this.getAttribute("data-id");
        if (action === "minus") updateQty(id, -1);
        else if (action === "plus") updateQty(id, 1);
        else if (action === "remove") removeFromCart(id);
      });
    });
  }

  function buildCheckoutUrl() {
    const total = getTotal();
    const desc = getDescription();
    const params = new URLSearchParams();
    params.set("amount", total.toFixed(2));
    if (desc) params.set("description", desc);
    return "/?" + params.toString();
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // Cart drawer toggle
  const cartToggle = document.getElementById("cartToggle");
  const cartClose = document.getElementById("cartClose");
  const cartDrawer = document.getElementById("cartDrawer");
  const cartOverlay = document.getElementById("cartOverlay");

  function openCart() {
    cartDrawer.classList.add("open");
    cartDrawer.setAttribute("aria-hidden", "false");
    cartOverlay.classList.add("visible");
    cartOverlay.setAttribute("aria-hidden", "false");
  }

  function closeCart() {
    cartDrawer.classList.remove("open");
    cartDrawer.setAttribute("aria-hidden", "true");
    cartOverlay.classList.remove("visible");
    cartOverlay.setAttribute("aria-hidden", "true");
  }

  if (cartToggle) cartToggle.addEventListener("click", openCart);
  if (cartClose) cartClose.addEventListener("click", closeCart);
  if (cartOverlay) cartOverlay.addEventListener("click", closeCart);

  // Add to cart buttons
  document.querySelectorAll(".btn-add").forEach((btn) => {
    btn.addEventListener("click", function () {
      const id = this.getAttribute("data-id");
      const name = this.getAttribute("data-name");
      const price = this.getAttribute("data-price");
      addToCart(id, name, price);
    });
  });

  // Init
  renderCart();
  updateCartCount();
})();
