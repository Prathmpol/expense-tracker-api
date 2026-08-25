/* =====================================================================
   SIGN-EASE / EXPENSE TRACKER FRONTEND
   Connected to FastAPI backend
===================================================================== */

const API_BASE = "http://127.0.0.1:8000";

const ENDPOINTS = {
  register: "/auth/register",
  login: "/auth/login",
  me: null,

  expenses: "/expenses",
  expenseById: (id) => `/expenses/${id}`,

  analyticsSummary: "/analytics/summary",
  analyticsByCategory: "/analytics/category",
  analyticsMonthlyTrend: "/analytics/monthly"
};

const apiBaseDisplay = document.getElementById("api-base-display");

if (apiBaseDisplay) {
  apiBaseDisplay.textContent = API_BASE;
}


/* =====================================================================
   STATE
===================================================================== */

let token = localStorage.getItem("ledger_token") || null;
let expenses = [];

let categoryChart = null;
let trendChart = null;


/* =====================================================================
   HELPERS
===================================================================== */

function showToast(message, isError = false) {
  const toast = document.getElementById("toast");

  if (!toast) return;

  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.remove("hidden");

  clearTimeout(showToast._t);

  showToast._t = setTimeout(() => {
    toast.classList.add("hidden");
  }, 3200);
}


async function apiFetch(path, options = {}) {
  const headers = Object.assign(
    {
      "Content-Type": "application/json"
    },
    options.headers || {}
  );

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    logout();
    throw new Error("Session expired — please log in again.");
  }

  let data = null;

  try {
    data = await response.json();
  } catch (_) {
    // Response may not contain JSON.
  }

  if (!response.ok) {
    const message =
      data &&
      (data.detail || data.message);

    throw new Error(
      typeof message === "string"
        ? message
        : JSON.stringify(
            message || `Request failed (${response.status})`
          )
    );
  }

  return data;
}


function formatCurrency(value) {
  const number = Number(value || 0);

  return (
    "₹" +
    number.toLocaleString("en-IN", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })
  );
}


function formatShortCurrency(value) {
  const number = Number(value || 0);

  if (number >= 10000000) {
    return `₹${(number / 10000000).toFixed(1)}Cr`;
  }

  if (number >= 100000) {
    return `₹${(number / 100000).toFixed(1)}L`;
  }

  if (number >= 1000) {
    return `₹${(number / 1000).toFixed(1)}K`;
  }

  return `₹${Math.round(number)}`;
}


/*
   Convert:

   2026-08
   2026-07

   into:

   Aug
   Jul
*/
function formatMonthLabel(month) {
  if (!month) return "";

  const parts = String(month).split("-");

  if (parts.length < 2) {
    return month;
  }

  const year = Number(parts[0]);
  const monthNumber = Number(parts[1]);

  if (!year || !monthNumber) {
    return month;
  }

  const date = new Date(year, monthNumber - 1, 1);

  return date.toLocaleDateString("en-IN", {
    month: "short"
  });
}


/*
   Get current month's date range.
*/
function getCurrentMonthRange() {
  const now = new Date();

  const year = now.getFullYear();
  const month = now.getMonth();

  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);

  function formatDate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");

    return `${y}-${m}-${d}`;
  }

  return {
    start_date: formatDate(firstDay),
    end_date: formatDate(lastDay)
  };
}


/* =====================================================================
   AUTH SCREEN — TABS
===================================================================== */

document.querySelectorAll(".tab-btn").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.classList.remove("active");
      btn.setAttribute("aria-selected", "false");
    });

    button.classList.add("active");
    button.setAttribute("aria-selected", "true");

    const tab = button.dataset.tab;

    document
      .getElementById("login-form")
      .classList.toggle("hidden", tab !== "login");

    document
      .getElementById("register-form")
      .classList.toggle("hidden", tab !== "register");
  });
});


/* =====================================================================
   REGISTER
===================================================================== */

document
  .getElementById("register-form")
  .addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = document.getElementById("register-msg");

    message.textContent = "";
    message.className = "form-msg";

    const name = document
      .getElementById("register-name")
      .value
      .trim();

    const email = document
      .getElementById("register-email")
      .value
      .trim();

    const password =
      document.getElementById("register-password").value;

    if (!name || !email || !password) {
      message.textContent = "Please fill all fields.";
      message.classList.add("error");
      return;
    }

    try {
      await apiFetch(ENDPOINTS.register, {
        method: "POST",
        body: JSON.stringify({
          name,
          email,
          password
        })
      });

      message.textContent =
        "Account created — you can log in now.";

      message.classList.add("success");

      document
        .querySelector('.tab-btn[data-tab="login"]')
        .click();

      document.getElementById("login-email").value = email;

    } catch (error) {
      message.textContent = error.message;
      message.classList.add("error");
    }
  });


/* =====================================================================
   LOGIN
===================================================================== */

document
  .getElementById("login-form")
  .addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = document.getElementById("login-msg");

    message.textContent = "";
    message.className = "form-msg";

    const email = document
      .getElementById("login-email")
      .value
      .trim();

    const password =
      document.getElementById("login-password").value;

    if (!email || !password) {
      message.textContent =
        "Please enter your email and password.";

      message.classList.add("error");

      return;
    }

    try {
      const data = await apiFetch(ENDPOINTS.login, {
        method: "POST",
        body: JSON.stringify({
          email,
          password
        })
      });

      token = data.access_token;

      if (!token) {
        throw new Error(
          "Login succeeded but no access_token was returned."
        );
      }

      localStorage.setItem("ledger_token", token);

      await enterDashboard(email);

    } catch (error) {
      message.textContent = error.message;
      message.classList.add("error");
    }
  });


/* =====================================================================
   LOGOUT
===================================================================== */

document
  .getElementById("logout-btn")
  .addEventListener("click", logout);


function logout() {
  token = null;

  localStorage.removeItem("ledger_token");

  document
    .getElementById("dashboard-screen")
    .classList.add("hidden");

  document
    .getElementById("auth-screen")
    .classList.remove("hidden");
}


/* =====================================================================
   ENTER DASHBOARD
===================================================================== */

async function enterDashboard(username) {
  document
    .getElementById("auth-screen")
    .classList.add("hidden");

  document
    .getElementById("dashboard-screen")
    .classList.remove("hidden");

  document.getElementById("user-greeting").textContent =
    username
      ? `Signed in as ${username}`
      : "Signed in";

  const dateInput =
    document.getElementById("expense-date");

  if (dateInput) {
    dateInput.valueAsDate = new Date();
  }

  await loadExpenses();

  await loadAnalytics();
}


/* =====================================================================
   EXPENSES — LOAD
===================================================================== */

async function loadExpenses() {
  try {
    const data = await apiFetch(
      ENDPOINTS.expenses,
      {
        method: "GET"
      }
    );

    if (Array.isArray(data)) {
      expenses = data;
    } else {
      expenses =
        data.items ||
        data.expenses ||
        [];
    }

    renderExpenseTable(expenses);

  } catch (error) {
    showToast(error.message, true);
  }
}


/* =====================================================================
   EXPENSE TABLE
===================================================================== */

function renderExpenseTable(list) {
  const body =
    document.getElementById("expense-table-body");

  body.innerHTML = "";

  if (!list.length) {
    body.innerHTML = `
      <tr class="empty-row">
        <td colspan="5">
          No entries yet — add your first one above.
        </td>
      </tr>
    `;

    return;
  }

  list
    .slice()
    .sort(
      (a, b) =>
        new Date(b.date) -
        new Date(a.date)
    )
    .forEach((expense) => {
      const row = document.createElement("tr");

      row.innerHTML = `
        <td>${expense.date || ""}</td>

        <td>
          <span class="cat-pill">
            ${expense.category || "Other"}
          </span>
        </td>

        <td>
          ${expense.description || "—"}
        </td>

        <td class="num">
          ${formatCurrency(expense.amount)}
        </td>

        <td>
          <div class="row-actions">

            <button
              class="icon-btn"
              data-action="edit"
              data-id="${expense.id}"
              title="Edit"
            >
              Edit
            </button>

            <button
              class="icon-btn danger"
              data-action="delete"
              data-id="${expense.id}"
              title="Delete"
            >
              Delete
            </button>

          </div>
        </td>
      `;

      body.appendChild(row);
    });
}


/* =====================================================================
   EDIT / DELETE EXPENSE
===================================================================== */

document
  .getElementById("expense-table-body")
  .addEventListener("click", async (event) => {

    const button =
      event.target.closest(
        "button[data-action]"
      );

    if (!button) return;

    const id = button.dataset.id;


    /* ---------------------------------------------------------------
       EDIT
    --------------------------------------------------------------- */

    if (button.dataset.action === "edit") {
      const expense =
        expenses.find(
          (item) =>
            String(item.id) === String(id)
        );

      if (!expense) return;

      document.getElementById("expense-id").value =
        expense.id;

      document.getElementById("expense-amount").value =
        expense.amount;

      document.getElementById("expense-category").value =
        expense.category;

      document.getElementById("expense-date").value =
        expense.date;

      document.getElementById("expense-description").value =
        expense.description || "";

      document.getElementById(
        "expense-submit-btn"
      ).textContent = "Save changes";

      document
        .getElementById("expense-cancel-btn")
        .classList.remove("hidden");

      return;
    }


    /* ---------------------------------------------------------------
       DELETE
    --------------------------------------------------------------- */

    if (button.dataset.action === "delete") {
      if (!confirm("Delete this entry?")) {
        return;
      }

      try {
        await apiFetch(
          ENDPOINTS.expenseById(id),
          {
            method: "DELETE"
          }
        );

        showToast("Entry deleted.");

        await loadExpenses();

        await loadAnalytics();

      } catch (error) {
        showToast(
          error.message,
          true
        );
      }
    }
  });


/* =====================================================================
   RESET EXPENSE FORM
===================================================================== */

document
  .getElementById("expense-cancel-btn")
  .addEventListener(
    "click",
    resetExpenseForm
  );


function resetExpenseForm() {
  document
    .getElementById("expense-form")
    .reset();

  document.getElementById("expense-id").value =
    "";

  document.getElementById(
    "expense-date"
  ).valueAsDate = new Date();

  document.getElementById(
    "expense-submit-btn"
  ).textContent = "Add entry";

  document
    .getElementById("expense-cancel-btn")
    .classList.add("hidden");
}


/* =====================================================================
   CREATE / UPDATE EXPENSE
===================================================================== */

document
  .getElementById("expense-form")
  .addEventListener("submit", async (event) => {

    event.preventDefault();

    const message =
      document.getElementById("expense-msg");

    message.textContent = "";
    message.className = "form-msg";

    const id =
      document.getElementById("expense-id").value;

    const amount =
      parseFloat(
        document.getElementById(
          "expense-amount"
        ).value
      );

    const category =
      document.getElementById(
        "expense-category"
      ).value;

    const date =
      document.getElementById(
        "expense-date"
      ).value;

    const description =
      document.getElementById(
        "expense-description"
      ).value.trim();

    if (!amount || amount <= 0) {
      message.textContent =
        "Please enter a valid positive amount.";

      message.classList.add("error");

      return;
    }

    if (!category) {
      message.textContent =
        "Please select a category.";

      message.classList.add("error");

      return;
    }

    if (!date) {
      message.textContent =
        "Please select a date.";

      message.classList.add("error");

      return;
    }

    const payload = {
      amount,
      category,
      date,
      description
    };

    try {

      if (id) {
        await apiFetch(
          ENDPOINTS.expenseById(id),
          {
            method: "PUT",
            body: JSON.stringify(payload)
          }
        );

        showToast("Entry updated.");
      }

      else {
        await apiFetch(
          ENDPOINTS.expenses,
          {
            method: "POST",
            body: JSON.stringify(payload)
          }
        );

        showToast("Entry added.");
      }

      resetExpenseForm();

      await loadExpenses();

      await loadAnalytics();

    } catch (error) {
      message.textContent =
        error.message;

      message.classList.add("error");
    }
  });


/* =====================================================================
   EXPENSE SEARCH / FILTER
===================================================================== */

document
  .getElementById("expense-search")
  .addEventListener("input", (event) => {

    const query =
      event.target.value
        .toLowerCase()
        .trim();

    const filtered =
      expenses.filter((expense) => {

        const category =
          (expense.category || "")
            .toLowerCase();

        const description =
          (expense.description || "")
            .toLowerCase();

        return (
          category.includes(query) ||
          description.includes(query)
        );
      });

    renderExpenseTable(filtered);
  });


/* =====================================================================
   ANALYTICS
===================================================================== */

async function loadAnalytics() {

  let summary;
  let byCategory;
  let trend;


  /* ---------------------------------------------------------------
     SUMMARY
  --------------------------------------------------------------- */

  try {

    const range =
      getCurrentMonthRange();

    const params =
      new URLSearchParams({
        start_date: range.start_date,
        end_date: range.end_date
      });

    summary =
      await apiFetch(
        `${ENDPOINTS.analyticsSummary}?${params.toString()}`
      );

  } catch (error) {

    summary =
      computeSummary(expenses);
  }


  /* ---------------------------------------------------------------
     CATEGORY
  --------------------------------------------------------------- */

  try {

    byCategory =
      await apiFetch(
        ENDPOINTS.analyticsByCategory
      );

  } catch (error) {

    byCategory =
      computeByCategory(expenses);
  }


  /* ---------------------------------------------------------------
     MONTHLY TREND
  --------------------------------------------------------------- */

  try {

    trend =
      await apiFetch(
        ENDPOINTS.analyticsMonthlyTrend
      );

  } catch (error) {

    trend =
      computeMonthlyTrend(expenses);
  }


  renderSummary(summary);

  renderCategoryChart(byCategory);

  renderTrendChart(trend);
}


/* =====================================================================
   FALLBACK SUMMARY
===================================================================== */

function computeSummary(list) {

  const currentRange =
    getCurrentMonthRange();

  const monthlyExpenses =
    list.filter((expense) => {

      const date = expense.date || "";

      return (
        date >= currentRange.start_date &&
        date <= currentRange.end_date
      );
    });


  const source =
    monthlyExpenses.length
      ? monthlyExpenses
      : list;


  const totalExpenses =
    source.reduce(
      (sum, expense) =>
        sum + Number(expense.amount || 0),
      0
    );


  const categoryData =
    computeByCategory(source);


  const topCategory =
    categoryData.reduce(
      (best, item) => {

        if (
          !best ||
          item.total > best.total
        ) {
          return item;
        }

        return best;
      },
      null
    );


  const uniqueDates =
    new Set(
      source
        .map((expense) => expense.date)
        .filter(Boolean)
    );


  const daySpan =
    Math.max(uniqueDates.size, 1);


  return {
    total_income: 0,

    total_expenses:
      totalExpenses,

    balance:
      -totalExpenses,

    savings_rate: 0,

    highest_spending_category:
      topCategory
        ? topCategory.category
        : null,

    average_daily_spending:
      totalExpenses / daySpan
  };
}


/* =====================================================================
   FALLBACK CATEGORY ANALYTICS
===================================================================== */

function computeByCategory(list) {

  const categoryMap = {};


  list.forEach((expense) => {

    const category =
      expense.category || "Other";

    const amount =
      Number(expense.amount || 0);

    categoryMap[category] =
      (categoryMap[category] || 0) +
      amount;
  });


  const totalExpenses =
    Object.values(categoryMap)
      .reduce(
        (sum, value) =>
          sum + value,
        0
      );


  return Object.entries(categoryMap)
    .map(
      ([category, total]) => ({
        category,

        total,

        percentage:
          totalExpenses > 0
            ? (total / totalExpenses) * 100
            : 0,

        transaction_count:
          list.filter(
            (expense) =>
              (expense.category || "Other") ===
              category
          ).length
      })
    )
    .sort(
      (a, b) =>
        b.total - a.total
    );
}


/* =====================================================================
   FALLBACK MONTHLY ANALYTICS
===================================================================== */

function computeMonthlyTrend(list) {

  const monthlyMap = {};


  list.forEach((expense) => {

    const date =
      expense.date || "";

    const month =
      date.slice(0, 7);

    if (!month) return;

    monthlyMap[month] =
      (monthlyMap[month] || 0) +
      Number(expense.amount || 0);
  });


  return Object.entries(monthlyMap)
    .sort(
      ([monthA], [monthB]) =>
        monthA.localeCompare(monthB)
    )
    .map(
      ([month, totalExpenses]) => ({
        month,

        total_income: 0,

        total_expenses:
          totalExpenses,

        balance:
          -totalExpenses
      })
    );
}


/* =====================================================================
   SUMMARY CARDS
===================================================================== */

function renderSummary(summary) {

  document.getElementById(
    "stat-total"
  ).textContent =
    formatCurrency(
      summary.total_expenses
    );


  document.getElementById(
    "stat-count"
  ).textContent =
    expenses.length;


  document.getElementById(
    "stat-top-category"
  ).textContent =
    summary.highest_spending_category ||
    "—";


  document.getElementById(
    "stat-avg"
  ).textContent =
    formatCurrency(
      summary.average_daily_spending
    );
}


/* =====================================================================
   CATEGORY DONUT CHART
===================================================================== */

function renderCategoryChart(data) {

  const list =
    Array.isArray(data)
      ? data
      : (data.categories || []);


  const empty =
    document.getElementById(
      "category-chart-empty"
    );

  const canvas =
    document.getElementById(
      "category-chart"
    );


  if (!list.length) {

    empty.classList.remove("hidden");

    canvas.classList.add("hidden");

    if (categoryChart) {
      categoryChart.destroy();
      categoryChart = null;
    }

    return;
  }


  empty.classList.add("hidden");

  canvas.classList.remove("hidden");


  const palette = [
    "#12213A",
    "#C89B3C",
    "#B3532B",
    "#6E8B6E",
    "#8C7A5B",
    "#4C6584",
    "#A8875A",
    "#5E7A6C"
  ];


  if (categoryChart) {
    categoryChart.destroy();
  }


  categoryChart =
    new Chart(canvas, {

      type: "doughnut",

      data: {

        labels:
          list.map(
            (item) =>
              item.category
          ),

        datasets: [
          {
            data:
              list.map(
                (item) =>
                  Number(item.total || 0)
              ),

            backgroundColor:
              palette,

            borderWidth: 0,

            hoverOffset: 5
          }
        ]
      },


      options: {

        responsive: true,

        maintainAspectRatio: false,

        cutout: "68%",

        plugins: {

          legend: {

            position: "bottom",

            labels: {

              font: {
                family: "Inter",
                size: 11
              },

              color: "#12213A",

              padding: 12,

              usePointStyle: true,

              pointStyle: "circle"
            }
          },

          tooltip: {

            callbacks: {

              label: function (context) {

                const item =
                  list[context.dataIndex];

                const percentage =
                  Number(
                    item.percentage || 0
                  );

                return (
                  `${item.category}: ` +
                  `${formatCurrency(item.total)} ` +
                  `(${percentage.toFixed(1)}%)`
                );
              }
            }
          }
        }
      }
    });
}


/* =====================================================================
   MONTHLY SPENDING BAR CHART
===================================================================== */

function renderTrendChart(data) {

  /*
     Backend:

     {
       months: [
         {
           month: "2026-08",
           total_income: 0,
           total_expenses: 1400,
           balance: -1400
         }
       ]
     }
  */

  const list =
    Array.isArray(data)
      ? data
      : (data.months || []);


  const empty =
    document.getElementById(
      "trend-chart-empty"
    );

  const canvas =
    document.getElementById(
      "trend-chart"
    );


  /*
     ---------------------------------------------------------------
     NO DATA
     ---------------------------------------------------------------
  */

  if (!list.length) {

    empty.classList.remove("hidden");

    canvas.classList.add("hidden");

    if (trendChart) {
      trendChart.destroy();
      trendChart = null;
    }

    return;
  }


  /*
     ---------------------------------------------------------------
     DATA EXISTS
     ---------------------------------------------------------------
  */

  empty.classList.add("hidden");

  canvas.classList.remove("hidden");


  if (trendChart) {
    trendChart.destroy();
  }


  /*
     Sort months from oldest to newest.
  */

  const sortedList =
    list
      .slice()
      .sort(
        (a, b) =>
          String(a.month || "")
            .localeCompare(
              String(b.month || "")
            )
      );


  const labels =
    sortedList.map(
      (item) =>
        formatMonthLabel(item.month)
    );


  const values =
    sortedList.map(
      (item) =>
        Number(
          item.total_expenses || 0
        )
    );


  /*
     Find highest value so the chart can
     have a sensible y-axis.
  */

  const maxValue =
    Math.max(...values, 0);


  /*
     Add a little breathing room above
     the highest bar.
  */

  const suggestedMax =
    maxValue > 0
      ? Math.ceil(
          (maxValue * 1.2) / 100
        ) * 100
      : 100;


  trendChart =
    new Chart(canvas, {

      type: "bar",

      data: {

        labels,

        datasets: [
          {

            label: "Monthly spending",

            data: values,

            backgroundColor:
              "#B3532B",

            borderColor:
              "#B3532B",

            borderWidth: 0,

            borderRadius: 7,

            borderSkipped: false,

            maxBarThickness: 48
          }
        ]
      },


      options: {

        responsive: true,

        maintainAspectRatio: false,


        animation: {
          duration: 700
        },


        interaction: {
          intersect: false,
          mode: "index"
        },


        plugins: {

          legend: {
            display: false
          },


          tooltip: {

            displayColors: false,

            backgroundColor:
              "#12213A",

            titleFont: {
              family: "Inter",
              size: 12,
              weight: "600"
            },

            bodyFont: {
              family: "IBM Plex Mono",
              size: 12
            },

            padding: 12,

            callbacks: {

              title: function (items) {

                if (!items.length) {
                  return "";
                }

                return (
                  "Spending — " +
                  items[0].label
                );
              },

              label: function (context) {

                return (
                  " " +
                  formatCurrency(
                    context.raw
                  )
                );
              }
            }
          }
        },


        scales: {

          x: {

            grid: {
              display: false
            },

            border: {
              display: false
            },

            ticks: {

              color: "#6B7280",

              font: {
                family: "IBM Plex Mono",
                size: 10
              },

              padding: 8
            }
          },


          y: {

            beginAtZero: true,

            suggestedMax,

            border: {
              display: false
            },

            grid: {

              color:
                "rgba(18,33,58,0.08)",

              drawTicks: false
            },

            ticks: {

              color: "#6B7280",

              font: {
                family: "IBM Plex Mono",
                size: 10
              },

              padding: 8,

              callback: function (value) {
                return formatShortCurrency(value);
              }
            }
          }
        }
      }
    });
}


/* =====================================================================
   BOOTSTRAP
===================================================================== */

if (token) {

  enterDashboard("")
    .catch((error) => {

      console.error(
        "Dashboard startup failed:",
        error
      );

      logout();
    });
}