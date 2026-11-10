// RecipeNest - form validation with plain JavaScript (events + DOM).
// The same rules are checked again by Django in recipes/forms.py.
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("recipe-form");
  if (!form) return;

  const MAX_BYTES = 5 * 1024 * 1024;
  const HTTPS_LINK = /^https:\/\/\S+$/i;
  const fields = {
    title: form.querySelector("[name='title']"),
    cook_time: form.querySelector("[name='cook_time']"),
    ingredients: form.querySelector("[name='ingredients']"),
    steps: form.querySelector("[name='steps']"),
    image: form.querySelector("[name='image']"),
    image_url: form.querySelector("[name='image_url']"),
  };
  const preview = document.getElementById("image-preview");
  let linkFailed = false;

  function feedbackFor(name) {
    return form.querySelector(".invalid-feedback[data-for='" + name + "']");
  }

  function showError(name, message) {
    fields[name].classList.add("is-invalid");
    feedbackFor(name).textContent = message;
  }

  function clearError(name) {
    fields[name].classList.remove("is-invalid");
    feedbackFor(name).classList.remove("d-block");
    feedbackFor(name).textContent = "";
  }

  function countLines(text) {
    return text.split("\n").filter(function (line) { return line.trim() !== ""; }).length;
  }

  // Errors sent back by Django: highlight those fields too
  Object.keys(fields).forEach(function (name) {
    if (feedbackFor(name).textContent.trim() !== "") fields[name].classList.add("is-invalid");
    fields[name].addEventListener("input", function () { clearError(name); });
  });

  function checkFile() {
    const file = fields.image.files[0];
    if (!file) return true;
    if (!["image/jpeg", "image/png"].includes(file.type)) {
      showError("image", "Choose a JPG or PNG photo.");
      return false;
    }
    if (file.size > MAX_BYTES) {
      showError("image", "Choose a photo smaller than 5 MB.");
      return false;
    }
    return true;
  }

  function validate() {
    let ok = true;

    if (fields.title.value.trim().length < 3) {
      showError("title", "Enter a recipe name of at least 3 characters.");
      ok = false;
    }

    const minutes = Number(fields.cook_time.value);
    if (fields.cook_time.value.trim() === "" || !Number.isInteger(minutes) || minutes < 1 || minutes > 600) {
      showError("cook_time", "Enter the cooking time in whole minutes, between 1 and 600.");
      ok = false;
    }

    if (countLines(fields.ingredients.value) < 2) {
      showError("ingredients", "Add at least 2 ingredients, one per line.");
      ok = false;
    }

    if (countLines(fields.steps.value) < 1) {
      showError("steps", "Add at least one step.");
      ok = false;
    }

    if (!checkFile()) ok = false;

    const link = fields.image_url.value.trim();
    if (link && !HTTPS_LINK.test(link)) {
      showError("image_url", "Paste a full image link that starts with https://");
      ok = false;
    } else if (link && linkFailed) {
      showError("image_url", "This link didn’t load as an image. Check that it ends in .jpg, .png or .webp.");
      ok = false;
    }

    return ok;
  }

  form.addEventListener("submit", function (event) {
    if (!validate()) {
      event.preventDefault();
      const firstBad = form.querySelector(".is-invalid");
      if (firstBad) firstBad.focus();
    }
  });

  // Live preview of the chosen photo (DOM manipulation)
  fields.image.addEventListener("change", function () {
    clearError("image");
    const file = fields.image.files[0];
    if (file && checkFile()) {
      preview.onerror = null;
      preview.src = URL.createObjectURL(file);
      preview.hidden = false;
    } else if (!file) {
      showLinkPreview();
    } else {
      preview.hidden = true;
    }
  });

  // Preview a pasted image link; show an error if it doesn't load
  function showLinkPreview() {
    const link = fields.image_url.value.trim();
    linkFailed = false;
    if (fields.image.files[0] || !HTTPS_LINK.test(link)) {
      if (!fields.image.files[0]) preview.hidden = true;
      return;
    }
    preview.onerror = function () {
      linkFailed = true;
      preview.hidden = true;
      showError("image_url", "This link didn’t load as an image. Check that it ends in .jpg, .png or .webp.");
    };
    preview.onload = function () { linkFailed = false; };
    preview.src = link;
    preview.hidden = false;
  }

  fields.image_url.addEventListener("change", function () {
    const link = fields.image_url.value.trim();
    if (link && !HTTPS_LINK.test(link)) {
      showError("image_url", "Paste a full image link that starts with https://");
      preview.hidden = true;
      return;
    }
    showLinkPreview();
  });
  fields.image_url.addEventListener("input", function () { linkFailed = false; });

  // Editing a recipe that already has a link: show it
  if (fields.image_url.value.trim()) showLinkPreview();
});
