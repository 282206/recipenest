// RecipeNest - cook mode on the recipe page: tick off ingredients, tap steps as you
// finish them (progress bar + current step), and a two-click Delete button.
document.addEventListener("DOMContentLoaded", function () {
  "use strict";

  // Ingredients: tap to tick
  document.querySelectorAll(".ing-item").forEach(function (item) {
    item.addEventListener("click", function () {
      item.setAttribute("aria-pressed", String(item.getAttribute("aria-pressed") !== "true"));
    });
  });

  // Steps: tap (or Enter / Space) to mark done
  var steps = Array.prototype.slice.call(document.querySelectorAll("#steps li"));
  var bar = document.getElementById("cook-bar");
  var label = document.getElementById("cook-label");
  var doneBox = document.getElementById("cook-done");

  function update() {
    var done = steps.filter(function (li) { return li.classList.contains("done"); }).length;
    steps.forEach(function (li) { li.classList.remove("current"); });
    var next = steps.find(function (li) { return !li.classList.contains("done"); });
    if (next) next.classList.add("current");
    bar.style.width = (steps.length ? done / steps.length * 100 : 0) + "%";
    label.textContent = done ? done + " of " + steps.length + " steps done" : "Tap a step when it’s done";
    doneBox.classList.toggle("show", steps.length > 0 && done === steps.length);
  }

  steps.forEach(function (li) {
    function toggle() {
      li.classList.toggle("done");
      li.setAttribute("aria-pressed", String(li.classList.contains("done")));
      update();
    }
    li.addEventListener("click", toggle);
    li.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        toggle();
      }
    });
  });

  // Delete: first click asks, second click sends the POST form
  var del = document.getElementById("d-delete");
  var form = document.getElementById("delete-form");
  var resetTimer = null;
  if (del && form) {
    del.addEventListener("click", function (event) {
      event.preventDefault();
      if (del.classList.contains("confirming")) {
        form.submit();
        return;
      }
      del.classList.add("confirming");
      del.textContent = "Click again to delete";
      clearTimeout(resetTimer);
      resetTimer = setTimeout(function () {
        del.classList.remove("confirming");
        del.textContent = "Delete";
      }, 3000);
    });
  }
});
