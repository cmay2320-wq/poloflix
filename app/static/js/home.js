// Home page hero carousel: auto-advance + dot navigation
document.addEventListener("DOMContentLoaded", () => {
  const hero = document.getElementById("hero");
  if (!hero) return;

  const slides = Array.from(hero.querySelectorAll(".hero__slide"));
  const dots = Array.from(hero.querySelectorAll(".hero__dot"));
  if (slides.length < 2) return;

  let current = 0;
  let timer = setInterval(next, 7000);

  function goTo(index) {
    slides[current].classList.remove("is-active");
    dots[current] && dots[current].classList.remove("is-active");
    current = (index + slides.length) % slides.length;
    slides[current].classList.add("is-active");
    dots[current] && dots[current].classList.add("is-active");
  }

  function next() {
    goTo(current + 1);
  }

  dots.forEach((dot, i) => {
    dot.addEventListener("click", () => {
      goTo(i);
      clearInterval(timer);
      timer = setInterval(next, 7000);
    });
  });
});
