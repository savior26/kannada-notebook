document.querySelectorAll("[data-password-toggle]").forEach((button) => {
  button.addEventListener("click", () => {
    const input = document.getElementById(button.dataset.passwordToggle);
    if (!input) return;

    const reveal = input.type === "password";
    input.type = reveal ? "text" : "password";
    button.setAttribute("aria-pressed", String(reveal));
    button.setAttribute("aria-label", reveal ? "Hide password" : "Show password");
  });
});

const registrationForm = document.getElementById("register-form");
registrationForm?.addEventListener("submit", (event) => {
  const password = document.getElementById("password");
  const confirmation = document.getElementById("confirm-password");
  if (password.value !== confirmation.value) {
    event.preventDefault();
    confirmation.setCustomValidity("The passwords do not match.");
    confirmation.reportValidity();
  } else {
    confirmation.setCustomValidity("");
  }
});

document.getElementById("confirm-password")?.addEventListener("input", (event) => {
  event.currentTarget.setCustomValidity("");
});
