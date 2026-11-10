// RecipeNest - builds recipe cards in the browser (jQuery search results, Saved page).
// The HTML matches the Django templates _card.html and _photo.html exactly.
window.RN = window.RN || {};

(function (RN) {
  "use strict";

  var CLOCK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>';
  var HEART = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.5s-7.5-4.4-9.3-9.2C1.4 7.6 3.9 4 7.4 4c2 0 3.5 1.1 4.6 2.6C13.1 5.1 14.6 4 16.6 4c3.5 0 6 3.6 4.7 7.3-1.8 4.8-9.3 9.2-9.3 9.2z" fill="none" stroke="currentColor" stroke-width="2"/></svg>';

  function esc(text) {
    return String(text).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function plural(n, word) {
    return n + " " + word + (n === 1 ? "" : "s");
  }

  function mark(isVeg) {
    return isVeg
      ? '<span class="food-mark veg" role="img" aria-label="Veg"></span>'
      : '<span class="food-mark nonveg" role="img" aria-label="Non-veg"></span>';
  }

  function photoHtml(r, cls) {
    var letter = esc(r.title.charAt(0));
    if (!r.image) {
      return '<div class="' + cls + " placeholder-photo" + (r.is_veg ? "" : " nonveg") + '" aria-hidden="true">' + letter + "</div>";
    }
    return '<img class="' + cls + '" src="' + esc(r.image) + '" alt="' + esc(r.title) + '" loading="lazy" decoding="async"' +
      ' data-letter="' + letter + '"' + (r.is_veg ? "" : ' data-nonveg="1"') + ' onerror="rnPhotoFail(this)">';
  }

  function cardHtml(r, i) {
    return (
      '<article class="rcard card-in" style="--i:' + Math.min(i || 0, 10) + '">' +
        '<div class="rcard-media">' +
          photoHtml(r, "recipe-photo") +
          '<span class="chip-cuisine">' + esc(r.cuisine_emoji) + " " + esc(r.cuisine) + "</span>" +
          '<span class="time-badge">' + CLOCK + r.cook_time + " min</span>" +
          '<button class="fav" type="button" data-fav="' + r.id + '" data-title="' + esc(r.title) + '" aria-pressed="false" aria-label="Save ' + esc(r.title) + '">' + HEART + "</button>" +
        "</div>" +
        '<div class="rcard-body">' +
          '<h3 class="rcard-title"><a class="rcard-link" href="/recipe/' + r.id + '/">' + mark(r.is_veg) + esc(r.title) + "</a></h3>" +
          '<p class="rcard-meta">' + plural(r.ingredients.length, "ingredient") + ", " + plural(r.steps.length, "step") + "</p>" +
        "</div>" +
      "</article>"
    );
  }

  function gridCardHtml(r, i) {
    return '<div class="col-sm-6 col-lg-4 col-xl-3">' + cardHtml(r, i) + "</div>";
  }

  RN.esc = esc;
  RN.cardHtml = cardHtml;
  RN.gridCardHtml = gridCardHtml;
})(window.RN);
