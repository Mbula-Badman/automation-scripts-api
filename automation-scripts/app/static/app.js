const searchInput = document.querySelector("#script-search");
const categoryFilter = document.querySelector("#category-filter");
const languageFilter = document.querySelector("#language-filter");
const scriptCards = [...document.querySelectorAll(".card[data-name]")];
const resultCount = document.querySelector("#result-count");
const filterEmpty = document.querySelector("#filter-empty");

function updateScriptFilters() {
  const query = searchInput.value.trim().toLocaleLowerCase();
  const category = categoryFilter.value;
  const language = languageFilter.value;
  let visibleCount = 0;

  for (const card of scriptCards) {
    const matchesQuery = ["name", "description", "category", "language"]
      .some((field) => card.dataset[field].includes(query));
    const matchesCategory = !category || card.dataset.category === category;
    const matchesLanguage = !language || card.dataset.language === language;
    const visible = matchesQuery && matchesCategory && matchesLanguage;

    card.hidden = !visible;
    if (visible) visibleCount += 1;
  }

  resultCount.textContent = visibleCount;
  filterEmpty.hidden = visibleCount !== 0 || scriptCards.length === 0;
}

if (searchInput && categoryFilter && languageFilter && resultCount && filterEmpty) {
  searchInput.addEventListener("input", updateScriptFilters);
  categoryFilter.addEventListener("change", updateScriptFilters);
  languageFilter.addEventListener("change", updateScriptFilters);
}
