// RecipeNest - saved recipes (hearts) kept in localStorage, the nav count badge,
// toast messages, and the /saved/ page.
window.RN = window.RN || {};

(function (RN) {
  "use strict";

  var KEY = "rn-favs";

  function readIds() {
    try {
      var ids = JSON.parse(localStorage.getItem(KEY) || "[]");
      return Array.isArray(ids) ? ids.filter(function (id) { return Number.isInteger(id); }) : [];
    } catch (e) {
      return [];
    }
  }

  function writeIds(ids) {
    try {
      localStorage.setItem(KEY, JSON.stringify(ids));
      return true;
    } catch (e) {
      return false;
    }
  }

  var favs = readIds();
  var storageOk = true;

  // ---------- Toast ----------
  var toastTimer = null;
  function toast(message) {
    var box = document.getElementById("toast");
    if (!box) return;
    box.hidden = true;
    void box.offsetWidth;            // restart the slide-in animation
    box.textContent = message;
    box.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { box.hidden = true; }, 2800);
  }

  // ---------- Hearts ----------
  function updateBadge() {
    var badge = document.getElementById("saved-count");
    if (badge) badge.textContent = favs.length ? String(favs.length) : "";
  }

  function setButton(btn, on) {
    var title = btn.dataset.title || "recipe";
    btn.setAttribute("aria-pressed", String(on));
    if (btn.classList.contains("fav")) btn.setAttribute("aria-label", (on ? "Remove from saved " : "Save ") + title);
    if (btn.classList.contains("btn-save")) btn.textContent = on ? "♥ Saved" : "♡ Save recipe";
  }

  // Show the right state on every heart inside `root` (call again after adding cards)
  function sync(root) {
    (root || document).querySelectorAll("[data-fav]").forEach(function (btn) {
      setButton(btn, favs.indexOf(Number(btn.dataset.fav)) !== -1);
    });
  }

  function toggle(btn) {
    var id = Number(btn.dataset.fav);
    var on = favs.indexOf(id) === -1;
    favs = on ? [id].concat(favs) : favs.filter(function (x) { return x !== id; });
    storageOk = writeIds(favs);
    updateBadge();
    document.querySelectorAll('[data-fav="' + id + '"]').forEach(function (b) { setButton(b, on); });
    if (btn.classList.contains("fav")) {
      btn.classList.remove("pop");
      void btn.offsetWidth;
      btn.classList.add("pop");
    }
    var title = btn.dataset.title || "recipe";
    toast(!storageOk ? "Saved for this visit only. Your browser storage is full or turned off."
      : on ? "Saved “" + title + "”." : "Removed “" + title + "” from saved.");
    if (!on && document.getElementById("saved-grid")) renderSaved();
  }

  document.addEventListener("click", function (event) {
    var btn = event.target.closest("[data-fav]");
    if (btn) {
      event.preventDefault();
      toggle(btn);
    }
  });

  // ---------- Saved page ----------
  function renderSaved() {
    var grid = document.getElementById("saved-grid");
    var empty = document.getElementById("saved-empty");
    if (!favs.length) {
      grid.innerHTML = empty.innerHTML;
      return;
    }
    $.getJSON(grid.dataset.api, { ids: favs.join(",") })
      .done(function (data) {
        // Forget recipes that were deleted since they were saved
        var found = data.recipes.map(function (r) { return r.id; });
        if (found.length !== favs.length) {
          favs = favs.filter(function (id) { return found.indexOf(id) !== -1; });
          writeIds(favs);
          updateBadge();
        }
        grid.innerHTML = data.recipes.length ? data.recipes.map(RN.gridCardHtml).join("") : empty.innerHTML;
        sync(grid);
      })
      .fail(function () {
        grid.innerHTML = '<div class="col-12"><div class="empty-state"><p>Couldn’t load your saved recipes. Check that the Django server is running, then refresh.</p></div></div>';
      });
  }

  RN.toast = toast;
  RN.favs = { sync: sync };

  document.addEventListener("DOMContentLoaded", function () {
    updateBadge();
    sync(document);
    if (document.getElementById("saved-grid")) renderSaved();
    // Django messages are rendered into the toast by base.html: hide them after a moment
    var box = document.getElementById("toast");
    if (box && !box.hidden) toastTimer = setTimeout(function () { box.hidden = true; }, 3500);
  });
})(window.RN);
