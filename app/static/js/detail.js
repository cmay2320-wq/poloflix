document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("rateForm");
  if (!form) return;
  const starsWrap = form.querySelector(".rate-stars");
  const stars = Array.from(form.querySelectorAll(".star"));
  const mediaType = form.dataset.mediaType;
  const mediaId = parseInt(form.dataset.mediaId, 10);
  let current = parseFloat(starsWrap.dataset.value || "0");

  paint(current);

  stars.forEach((star, i) => {
    star.addEventListener("mouseenter", () => paint(i + 1));
    star.addEventListener("mouseleave", () => paint(current));
    star.addEventListener("click", () => {
      current = i + 1;
      paint(current);
      fetch("/api/rating", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ media_type: mediaType, media_id: mediaId, score: current * 2 }),
      })
        .then((r) => r.json())
        .then(() => window.showToast && window.showToast("Thanks for rating!", "success"))
        .catch(() => {});
    });
  });

  function paint(value) {
    stars.forEach((star, i) => star.classList.toggle("is-filled", i < value));
  }
});
