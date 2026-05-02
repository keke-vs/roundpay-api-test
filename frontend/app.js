const state = {
  token: sessionStorage.getItem("roundpayToken") || "",
  account: null,
  transactions: [],
};

const $ = (selector) => document.querySelector(selector);
const authScreen = $("#auth-screen");
const appScreen = $("#app-screen");
const toast = $("#toast");

function requestId() {
  return `REQ-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
}

function notify(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2200);
}

function headers() {
  const result = { "Content-Type": "application/json" };
  if (state.token) {
    result.Authorization = `Bearer ${state.token}`;
  }
  return result;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      ...headers(),
      ...(options.headers || {}),
    },
  });
  const body = await response.json();
  if (!response.ok || body.code !== 0) {
    throw new Error(body.message || "request failed");
  }
  return body.data;
}

function showAuthenticated(isAuthenticated) {
  authScreen.classList.toggle("hidden", isAuthenticated);
  appScreen.classList.toggle("hidden", !isAuthenticated);
}

function payloadFromForm(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function formatAmount(value) {
  const amount = Number(value || 0);
  return `${amount < 0 ? "-" : "+"}¥${Math.abs(amount).toFixed(2)}`;
}

function amountClass(value) {
  return Number(value) < 0 ? "amount-out" : "amount-in";
}

function transactionTypeName(type) {
  return {
    TRANSFER_OUT: "转出",
    TRANSFER_IN: "转入",
    FUND_BUY: "基金购买",
  }[type] || type;
}

function updateAccountView() {
  const account = state.account;
  $("#user-name").textContent = account?.nickname || "-";
  $("#account-value").textContent = account?.account || "-";
  $("#balance-value").textContent =
    typeof account?.balance === "number" ? `¥${account.balance.toFixed(2)}` : "-";
  $("#mobile-value").textContent = account?.mobile || "-";
  $("#transaction-count").textContent = String(state.transactions.length);

  if (account) {
    $("#profile-form").nickname.value = account.nickname;
    $("#profile-form").mobile.value = account.mobile;
  }
}

function renderMiniTransactions() {
  const container = $("#recent-transactions");
  const items = state.transactions.slice(0, 4);
  if (items.length === 0) {
    container.innerHTML = '<div class="empty-state">暂无交易流水</div>';
    return;
  }

  container.innerHTML = "";
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "mini-row";
    row.innerHTML = `
      <span>${item.description}</span>
      <strong class="${amountClass(item.amount)}">${formatAmount(item.amount)}</strong>
    `;
    container.appendChild(row);
  });
}

function renderTransactionTable() {
  const tbody = $("#transaction-table");
  tbody.innerHTML = "";

  if (state.transactions.length === 0) {
    const row = document.createElement("tr");
    row.innerHTML = '<td colspan="5">暂无交易流水</td>';
    tbody.appendChild(row);
    return;
  }

  state.transactions.forEach((item) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${item.createdAt}</td>
      <td>${transactionTypeName(item.type)}</td>
      <td>${item.description}</td>
      <td class="${amountClass(item.amount)}">${formatAmount(item.amount)}</td>
      <td><span class="status success">${item.status}</span></td>
    `;
    tbody.appendChild(row);
  });
}

async function loadTransactions() {
  const data = await api("/api/transactions?limit=20");
  state.transactions = data.items;
  renderMiniTransactions();
  renderTransactionTable();
  updateAccountView();
}

async function loadAccount() {
  const [account] = await Promise.all([
    api("/api/account"),
    loadFunds(),
  ]);
  state.account = account;
  await loadTransactions();
  updateAccountView();
}

function activateView(viewId) {
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.view === viewId);
  });
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("active", view.id === viewId);
  });
  const active = document.querySelector(`.nav-item[data-view="${viewId}"]`);
  $("#page-title").textContent = active ? active.textContent : "首页";
}

function renderFunds(items) {
  const list = $("#fund-list");
  list.innerHTML = "";
  items.forEach((fund) => {
    const card = document.createElement("article");
    card.className = "fund-card";
    const statusClass = fund.status === "OPEN" ? "open" : "closed";
    const statusText = fund.status === "OPEN" ? "开放" : "关闭";
    card.innerHTML = `
      <header>
        <h3>${fund.name}</h3>
        <span class="status ${statusClass}">${statusText}</span>
      </header>
      <div class="fund-meta">
        <span>${fund.fundId}</span>
        <span>起购 ¥${Number(fund.minAmount).toFixed(2)}</span>
      </div>
      <button type="button" data-fund="${fund.fundId}" ${fund.status !== "OPEN" ? "disabled" : ""}>选择</button>
    `;
    list.appendChild(card);
  });

  list.querySelectorAll("[data-fund]").forEach((button) => {
    button.addEventListener("click", () => {
      $("#fund-buy-form").fundId.value = button.dataset.fund;
      notify(`已选择 ${button.dataset.fund}`);
    });
  });
}

async function loadFunds() {
  const data = await api("/api/funds?page=1&pageSize=10");
  renderFunds(data.items);
}

async function submitTransfer(form) {
  const payload = payloadFromForm(form);
  payload.amount = Number(payload.amount);
  payload.requestId = payload.requestId || requestId();
  await api("/api/transfer", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  $("#request-id").value = requestId();
  notify("转账成功");
  await loadAccount();
}

function bindNavigation() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => activateView(button.dataset.view));
  });
  document.querySelectorAll("[data-view-target]").forEach((button) => {
    button.addEventListener("click", () => activateView(button.dataset.viewTarget));
  });
}

function bindForms() {
  $("#login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const data = await api("/api/login", {
        method: "POST",
        body: JSON.stringify(payloadFromForm(event.currentTarget)),
      });
      state.token = data.token;
      sessionStorage.setItem("roundpayToken", data.token);
      showAuthenticated(true);
      await loadAccount();
      activateView("dashboard");
      notify("登录成功");
    } catch (error) {
      notify(error.message, true);
    }
  });

  $("#quick-transfer-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await submitTransfer(event.currentTarget);
    } catch (error) {
      notify(error.message, true);
    }
  });

  $("#transfer-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await submitTransfer(event.currentTarget);
    } catch (error) {
      notify(error.message, true);
    }
  });

  $("#profile-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await api("/api/profile", {
        method: "PATCH",
        body: JSON.stringify(payloadFromForm(event.currentTarget)),
      });
      notify("资料已保存");
      await loadAccount();
    } catch (error) {
      notify(error.message, true);
    }
  });

  $("#fund-buy-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = payloadFromForm(event.currentTarget);
    payload.amount = Number(payload.amount);
    try {
      await api("/api/fund/buy", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      notify("购买成功");
      await loadAccount();
      activateView("transactions");
    } catch (error) {
      notify(error.message, true);
    }
  });

  $("#logout-button").addEventListener("click", () => {
    state.token = "";
    state.account = null;
    state.transactions = [];
    sessionStorage.removeItem("roundpayToken");
    showAuthenticated(false);
    notify("已退出登录");
  });
}

async function restoreSession() {
  if (!state.token) {
    showAuthenticated(false);
    return;
  }

  showAuthenticated(true);
  try {
    await loadAccount();
    activateView("dashboard");
  } catch (error) {
    state.token = "";
    sessionStorage.removeItem("roundpayToken");
    showAuthenticated(false);
    notify("登录已失效", true);
  }
}

function init() {
  $("#request-id").value = requestId();
  bindNavigation();
  bindForms();
  restoreSession();
}

init();
