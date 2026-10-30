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

document.querySelector("[data-upload-form]")?.addEventListener("submit", (event) => {
  const fileInput = event.currentTarget.querySelector('input[type="file"]');
  if (!fileInput.files.length) {
    event.preventDefault();
    fileInput.reportValidity();
  }
});
