const searchInput = document.getElementById("notebook-search");
const cards = Array.from(document.querySelectorAll(".notebook-card"));
const noResults = document.getElementById("no-search-results");
searchInput?.addEventListener("input", () => {
  const query = searchInput.value.trim().toLocaleLowerCase();
  let visibleCount = 0;
  cards.forEach((card) => {
    const matches = card.dataset.search.includes(query);
    card.hidden = !matches;
    if (matches) visibleCount += 1;
  });
  if (noResults) noResults.hidden = visibleCount > 0;
});

document.querySelectorAll("[data-confirm]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});

document.querySelectorAll(".card-actions").forEach((menu) => {
  menu.addEventListener("toggle", () => {
    menu.closest(".notebook-card")?.classList.toggle("menu-open", menu.open);
    if (menu.open) document.querySelectorAll(".card-actions[open]").forEach((other) => {
      if (other !== menu) {
        other.open = false;
        other.closest(".notebook-card")?.classList.remove("menu-open");
      }
    });
  });
  menu.querySelector("[data-open-edit]")?.addEventListener("click", () => {
    const form = menu.querySelector(".rename-form");
    if (form) {
      form.hidden = false;
      menu.querySelector("[data-open-edit]").hidden = true;
      form.querySelector("input")?.focus();
    }
  });
});

document.querySelectorAll(".upload-button input[type=file]").forEach((input) => {
  input.addEventListener("change", () => {
    if (input.files.length) input.form.requestSubmit();
  });
});
