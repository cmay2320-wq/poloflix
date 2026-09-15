// ===========================================================================
// POLOFLIX - GLOBAL APP BEHAVIOUR
// ===========================================================================

document.addEventListener("DOMContentLoaded", () => {
  initToasts();
  initSearchSuggestions();
  initWatchlistButtons();
});

// ---------------------------------------------------------------------
// TOASTS - auto dismiss
// ---------------------------------------------------------------------
function initToasts() {
  const stack = document.getElementById("toastStack");
  if (!stack) return;
  Array.from(stack.children).forEach((toast) => {
    setTimeout(() => {
      toast.style.transition = "opacity .3s ease, transform .3s ease";
      toast.style.opacity = "0";
      toast.style.transform = "translateX(16px)";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  });
}

window.showToast = function (message, category = "info") {
  const stack = document.getElementById("toastStack");
  if (!stack) return;
  const toast = document.createElement("div");
  toast.className = `toast toast--${category}`;
  toast.textContent = message;
  stack.appendChild(toast);
  setTimeout(() => {
    toast.style.transition = "opacity .3s ease, transform .3s ease";
    toast.style.opacity = "0";
    toast.style.transform = "translateX(16px)";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
};

// ---------------------------------------------------------------------
// LIVE SEARCH SUGGESTIONS
// ---------------------------------------------------------------------
function initSearchSuggestions() {
  const input = document.getElementById("searchInput");
  const box = document.getElementById("searchSuggestions");
  if (!input || !box) return;

  let debounceTimer;
  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const q = input.value.trim();
    if (q.length < 2) {
      box.classList.remove("is-open");
      box.innerHTML = "";
      return;
    }
    debounceTimer = setTimeout(() => fetchSuggestions(q), 220);
  });

  input.addEventListener("focus", () => {
    if (box.innerHTML) box.classList.add("is-open");
  });

  document.addEventListener("click", (e) => {
    if (!box.contains(e.target) && e.target !== input) {
      box.classList.remove("is-open");
    }
  });

  function fetchSuggestions(q) {
    fetch(`/api/search/suggest?q=${encodeURIComponent(q)}`)
      .then((r) => r.json())
      .then((results) => {
        if (!results.length) {
          box.innerHTML = `<div class="sug-empty">No matches for "${escapeHtml(q)}"</div>`;
        } else {
          box.innerHTML = results
            .map(
              (r) =>
                `<a href="${r.url}"><span>${escapeHtml(r.title)}${r.year ? " (" + r.year + ")" : ""}</span><span class="sug-type">${r.type}</span></a>`
            )
            .join("");
        }
        box.classList.add("is-open");
      })
      .catch(() => {});
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---------------------------------------------------------------------
// WATCHLIST ("My List") TOGGLE BUTTONS
// ---------------------------------------------------------------------
function initWatchlistButtons() {
  document.querySelectorAll(".watchlist-btn").forEach((btn) => {
    const inList = btn.dataset.inList === "true";
    updateWatchlistBtn(btn, inList);

    btn.addEventListener("click", () => {
      const mediaType = btn.dataset.mediaType;
      const mediaId = parseInt(btn.dataset.mediaId, 10);
      if (!mediaType || !mediaId) return;

      fetch("/api/watchlist/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ media_type: mediaType, media_id: mediaId }),
      })
        .then((r) => {
          if (r.status === 401) {
            window.location.href = "/auth/login";
            throw new Error("not authenticated");
          }
          return r.json();
        })
        .then((data) => {
          btn.dataset.inList = data.in_list ? "true" : "false";
          updateWatchlistBtn(btn, data.in_list);
          window.showToast(data.in_list ? "Added to My List" : "Removed from My List", "success");
        })
        .catch(() => {});
    });
  });
}

function updateWatchlistBtn(btn, inList) {
  const label = btn.querySelector("span");
  if (label) label.textContent = inList ? "In My List" : "My List";
}
