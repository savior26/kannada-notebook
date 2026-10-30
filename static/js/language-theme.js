(() => {
  const languageNames = { en: "English", hi: "Hindi", kn: "Kannada" };
  let language = localStorage.getItem("response-language") || "en";
  if (!languageNames[language]) language = "en";
  let theme = localStorage.getItem("color-theme") || "dark";
  const setTheme = (value) => {
    theme = value === "light" ? "light" : "dark";
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document.body?.setAttribute("data-theme", theme);
    const themeColor = document.querySelector("[data-theme-color]");
    if (themeColor) themeColor.content = theme === "light" ? "#ffffff" : "#101010";
    localStorage.setItem("color-theme", theme);
    updateThemeButtons();
  };

  document.querySelectorAll("[data-language-picker]").forEach((picker) => {
    const trigger = picker.querySelector(".language-trigger");
    const current = picker.querySelector(".language-current");
    const menu = picker.querySelector(".language-menu");
    const search = picker.querySelector(".language-search");
    const options = Array.from(picker.querySelectorAll("[data-language]"));
    const select = (value) => {
      language = languageNames[value] ? value : "en";
      localStorage.setItem("response-language", language);
      current.textContent = languageNames[language];
      document.querySelectorAll("[data-response-language]").forEach((field) => { field.value = language; });
      options.forEach((option) => option.setAttribute("aria-selected", String(option.dataset.language === language)));
    };
    select(language);
    trigger.addEventListener("click", () => {
      const open = trigger.getAttribute("aria-expanded") !== "true";
      trigger.setAttribute("aria-expanded", String(open));
      menu.hidden = !open;
      if (open) search.focus();
    });
    options.forEach((option) => option.addEventListener("click", () => {
      select(option.dataset.language);
      menu.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
    }));
    search.addEventListener("input", () => {
      const term = search.value.trim().toLocaleLowerCase();
      options.forEach((option) => { option.hidden = !option.textContent.toLocaleLowerCase().includes(term); });
    });
    document.addEventListener("click", (event) => {
      if (!picker.contains(event.target)) {
        menu.hidden = true;
        trigger.setAttribute("aria-expanded", "false");
      }
    });
  });

  function updateThemeButtons() { document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    button.innerHTML = `<img class="theme-icon" src="/static/images/${next === "light" ? "sun" : "moon"}.png" alt="">`;
    button.setAttribute("aria-label", `Switch to ${next} theme`);
    button.title = `Switch to ${next} theme`;
  }); }
  setTheme(theme);
  updateThemeButtons();
  document.querySelectorAll("[data-theme-toggle]").forEach((button) => button.addEventListener("click", () => {
    setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  }));
})();
