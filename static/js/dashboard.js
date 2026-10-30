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

document.querySelectorAll(".upload-button input[type=file]").forEach((input) => {
  input.addEventListener("change", () => {
    if (input.files.length) input.form.requestSubmit();
  });
});
