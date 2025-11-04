document.addEventListener("DOMContentLoaded", () => {
  // Theme toggle logic
  const themeButtons = document.querySelectorAll(".theme-btn");

  function setActiveThemeButton(theme) {
    themeButtons.forEach(btn =>
      btn.classList.toggle("active", btn.id === "btn-" + theme)
    );
  }

  function applyTheme(theme) {
    document.body.className = theme + "-theme";
    setActiveThemeButton(theme);
    localStorage.setItem("selectedTheme", theme);
  }

  const savedTheme = localStorage.getItem("selectedTheme") || "blue";
  applyTheme(savedTheme);

  themeButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const theme = btn.id.replace("btn-", "");
      applyTheme(theme);
    });
  });

  // Input type toggle between URL and text
  const radioUrl = document.getElementById("radio-url");
  const radioText = document.getElementById("radio-text");
  const urlInput = document.getElementById("url_input");
  const textInput = document.getElementById("text_input");

  function toggleInput() {
    if (radioUrl && radioUrl.checked) {
      urlInput.style.display = "block";
      textInput.style.display = "none";
    } else {
      urlInput.style.display = "none";
      textInput.style.display = "block";
    }
  }

  if (radioUrl && radioText) {
    radioUrl.addEventListener("change", toggleInput);
    radioText.addEventListener("change", toggleInput);
    toggleInput();
  }
});
