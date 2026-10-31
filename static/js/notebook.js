const workspace = document.getElementById("workspace");
const revealSourcesButton = document.querySelector(".show-sources");
const languageField = document.querySelector("[data-response-language]");
const questionField = document.querySelector('[name="question"]');
const languageValue = () => localStorage.getItem("response-language") || "en";
if (languageField) languageField.value = languageValue();
document.querySelectorAll("[data-language]").forEach((option) => option.addEventListener("click", () => {
  if (languageField) languageField.value = option.dataset.language;
}));

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
document.querySelector("[data-speech-input]")?.addEventListener("click", () => {
  if (!SpeechRecognition) {
    window.alert("Speech recognition is not supported in this browser. Try a recent version of Chrome or Edge.");
    return;
  }
  const recognition = new SpeechRecognition();
  const language = languageValue();
  recognition.lang = ({ en: "en-IN", hi: "hi-IN", kn: "kn-IN" })[language] || "en-IN";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.onresult = (event) => {
    const spoken = event.results[0][0].transcript;
    questionField.value = `${questionField.value} ${spoken}`.trim();
    questionField.focus();
  };
  recognition.onerror = () => window.alert("Could not recognize speech. Check microphone permission and try again.");
  recognition.start();
});

document.querySelector("[data-speak-answer]")?.addEventListener("click", () => {
  const answers = Array.from(document.querySelectorAll(".answer-text"));
  if (!answers.length || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(answers[answers.length - 1].textContent);
  const language = languageValue();
  utterance.lang = ({ en: "en-IN", hi: "hi-IN", kn: "kn-IN" })[language] || "en-IN";
  window.speechSynthesis.speak(utterance);
});

document.querySelectorAll("[data-panel-toggle]").forEach((button) => {
  button.addEventListener("click", () => {
    const hidden = workspace.classList.toggle("sources-hidden");
    revealSourcesButton.hidden = !hidden;
    document.querySelector(".panel-toggle")?.setAttribute(
      "aria-label",
      hidden ? "Show sources panel" : "Hide sources panel",
    );
  });
});

function showProcessingSource(form) {
  const list = document.getElementById("source-list");
  if (!list) return;

  let sourceName = "Copied text.txt";
  const fileInput = form.querySelector('input[type="file"]');
  if (fileInput?.files?.length) {
    sourceName = fileInput.files[0].name;
  } else {
    const title = form.querySelector('[name="title"]')?.value.trim();
    if (title) sourceName = title.toLowerCase().endsWith(".txt") ? title : `${title}.txt`;
  }

  const row = document.createElement("li");
  row.className = "processing-source";
  row.setAttribute("role", "status");
  row.innerHTML = '<span class="processing-spinner" aria-hidden="true"></span><span class="processing-copy"><span class="processing-name"></span><span class="processing-stage">Uploading, processing and chunking…</span></span>';
  row.querySelector(".processing-name").textContent = sourceName;
  list.prepend(row);
  row.scrollIntoView({ behavior: "smooth", block: "nearest" });
  form.setAttribute("aria-busy", "true");
  form.querySelectorAll('button[type="submit"]').forEach((button) => {
    button.disabled = true;
    button.textContent = "Processing…";
  });
}

document.querySelectorAll("[data-processing-form]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    const fileInput = form.querySelector('input[type="file"]');
    if (fileInput && !fileInput.files.length) {
      event.preventDefault();
      fileInput.reportValidity();
      return;
    }
    showProcessingSource(form);
  });
});

document.querySelectorAll("[data-confirm]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});

document.querySelectorAll(".source-actions").forEach((menu) => {
  menu.addEventListener("toggle", () => {
    if (menu.open) document.querySelectorAll(".source-actions[open]").forEach((other) => {
      if (other !== menu) other.open = false;
    });
  });
  menu.querySelector("[data-open-rename]")?.addEventListener("click", () => {
    const form = menu.querySelector(".source-rename-form");
    if (form) {
      form.hidden = false;
      menu.querySelector("[data-open-rename]").hidden = true;
      form.querySelector("input")?.focus();
    }
  });
});

document.querySelectorAll(".source-rename-form").forEach((form) => {
  form.addEventListener("submit", () => {
    const input = form.querySelector("[data-file-extension]");
    if (input && !input.value.trim().toLocaleLowerCase().endsWith(input.dataset.fileExtension.toLocaleLowerCase())) {
      input.value = `${input.value.trim()}${input.dataset.fileExtension}`;
    }
  });
});

const newlyAddedSource = document.querySelector("[data-new-source='true']");
if (newlyAddedSource) {
  requestAnimationFrame(() => newlyAddedSource.scrollIntoView({ behavior: "smooth", block: "nearest" }));
}
