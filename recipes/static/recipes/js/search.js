// RecipeNest - home page: live ingredient search and filters with jQuery AJAX.
// Without JavaScript the same controls are plain links and GET forms (Django renders
// the page); with it, results come from /api/search/ and are drawn without a reload.
$(function () {
  "use strict";

  var PAGE = 24;
  var DEFAULTS = { q: "", type: "all", cuisine: "all", sort: "rec" };
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var $search = $("#search");
  var $grid = $("#recipe-grid");
  var $more = $("#show-more");
  var $featured = $("#featured");
  var $typeFilter = $(".type-filter");

  var state = readUrl();
  var limit = PAGE;
  var results = null;     // last API response
  var requestNo = 0;      // ignore answers to older requests

  function readUrl() {
    var params = new URLSearchParams(window.location.search);
    return {
      q: (params.get("q") || "").trim(),
      type: params.get("type") || "all",
      cuisine: params.get("cuisine") || "all",
      sort: params.get("sort") || "rec"
    };
  }

  // Same rules as home_url() in views.py: leave out default values
  function urlFor(s, hash) {
    var params = new URLSearchParams();
    Object.keys(DEFAULTS).forEach(function (key) {
      if (s[key] && s[key] !== DEFAULTS[key]) params.set(key, s[key]);
    });
    var query = params.toString();
    return "/" + (query ? "?" + query : "") + (hash === false ? "" : "#all-recipes");
  }

  function scrollToResults() {
    document.getElementById("all-recipes").scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth" });
  }

  // ---------- Sliding Veg / Non-veg pill ----------
  function movePill(animate) {
    var $pill = $typeFilter.find(".type-pill");
    var active = $typeFilter.find('a[aria-current="true"]')[0];
    if (!active || !active.offsetWidth) return;
    if (!animate) $pill.css("transition", "none");
    $pill.css({ width: active.offsetWidth + "px", transform: "translateX(" + (active.offsetLeft - 4) + "px)" });
    if (!animate) { void $pill[0].offsetWidth; $pill.css("transition", ""); }
  }
  $typeFilter.addClass("has-pill");
  movePill(false);
  $(window).on("resize", function () { movePill(false); });

  // ---------- Keep every link and control in step with the state ----------
  function syncControls() {
    $typeFilter.find("a[data-type]").each(function () {
      var value = this.dataset.type;
      this.href = urlFor($.extend({}, state, { type: value }));
      if (value === state.type) this.setAttribute("aria-current", "true"); else this.removeAttribute("aria-current");
    });
    $(".cuisine-tile").each(function () {
      var name = this.dataset.cuisine;
      var active = name === state.cuisine;
      this.href = urlFor($.extend({}, state, { cuisine: active || name === "all" ? "all" : name }));
      if (active) this.setAttribute("aria-current", "true"); else this.removeAttribute("aria-current");
    });
    $(".chip[data-chip]").each(function () {
      this.href = urlFor($.extend({}, state, { q: this.dataset.chip }));
    });
    $("#home-sort").val(state.sort);

    var tile = $('.cuisine-tile[data-cuisine="' + state.cuisine + '"]')[0];
    $("#active-cuisine").html(state.cuisine !== "all" && tile
      ? '<span class="active-filter">' + RN.esc(tile.dataset.emoji) + " " + RN.esc(state.cuisine) +
        ' <a href="' + urlFor($.extend({}, state, { cuisine: "all" })) + '" id="clear-cuisine" aria-label="Show all cuisines">×</a></span>'
      : "");
    $featured.prop("hidden", !!(state.q || state.type !== "all" || state.cuisine !== "all"));
    movePill(true);
  }

  // ---------- Draw the results ----------
  function render() {
    var list = results.recipes;
    $("#grid-title").text(results.title);
    $("#result-count").text(results.label);
    if (!list.length) {
      var message = state.q
        ? "No recipes match “" + RN.esc(state.q) + "” with these filters."
        : "No recipes match these filters.";
      $grid.html(
        '<div class="col-12"><div class="empty-state"><div class="big" aria-hidden="true">🥄</div>' +
        '<p class="mt-2">' + message + " Try another ingredient or clear a filter.</p>" +
        '<a class="btn btn-leaf" href="/recipe/add/">Add a recipe</a></div></div>'
      );
    } else {
      $grid.html(list.slice(0, limit).map(RN.gridCardHtml).join(""));
    }
    $more.prop("hidden", list.length <= limit);
    RN.favs.sync($grid[0]);
  }

  // Ask Django for the matching recipes (jQuery AJAX -> JSON)
  function load(history) {
    var mine = ++requestNo;
    syncControls();
    if (history === "push") window.history.pushState(state, "", urlFor(state, false));
    if (history === "replace") window.history.replaceState(state, "", urlFor(state, false));
    return $.ajax({
      url: "/api/search/",
      method: "GET",
      data: { ing: state.q, type: state.type, cuisine: state.cuisine, sort: state.sort },
      dataType: "json"
    })
      .done(function (data) {
        if (mine !== requestNo) return;
        results = data;
        render();
      })
      .fail(function () {
        if (mine === requestNo) $("#result-count").text("Search isn’t reachable right now. Check that the Django server is running.");
      });
  }

  function change(changes, history) {
    $.extend(state, changes);
    limit = PAGE;
    return load(history || "push");
  }

  // ---------- Events ----------
  var typingTimer = null;
  $search.on("input", function () {
    var query = $(this).val().trim();
    clearTimeout(typingTimer);
    typingTimer = setTimeout(function () { change({ q: query }, "replace"); }, 300);
  });
  $("#search-form").on("submit", function (event) {
    event.preventDefault();
    clearTimeout(typingTimer);
    change({ q: $search.val().trim() });
    scrollToResults();
  });

  $(".chip[data-chip]").on("click", function (event) {
    event.preventDefault();
    $search.val(this.dataset.chip);
    change({ q: this.dataset.chip });
    scrollToResults();
  });

  $typeFilter.on("click", "a[data-type]", function (event) {
    event.preventDefault();
    change({ type: this.dataset.type });
  });

  $("#cuisine-strip").on("click", ".cuisine-tile", function (event) {
    event.preventDefault();
    var name = this.dataset.cuisine;
    change({ cuisine: state.cuisine === name ? "all" : name });
    if (state.cuisine !== "all") scrollToResults();
  });

  $("#active-cuisine").on("click", "#clear-cuisine", function (event) {
    event.preventDefault();
    change({ cuisine: "all" });
  });

  $("#home-sort").on("change", function () {
    change({ sort: this.value });
  });
  $("#sort-form").on("submit", function (event) { event.preventDefault(); });

  // "Show more" adds the next 24 cards in place instead of opening ?page=2
  $more.on("click", function (event) {
    event.preventDefault();
    limit += PAGE;
    if (results) render(); else load(null);
  });

  window.addEventListener("popstate", function () {
    state = readUrl();
    $search.val(state.q);
    limit = PAGE;
    load(null);
  });

  // Surprise me: roll the dice, then open a random recipe
  $("#surprise").on("click", function (event) {
    var href = this.href;
    if (reduceMotion) return;
    event.preventDefault();
    $(this).removeClass("rolling");
    void this.offsetWidth;
    $(this).addClass("rolling");
    setTimeout(function () { window.location.href = href; }, 550);
  });

  // Rotating placeholder hint in the search box
  var hints = ["paneer", "noodles", "tomato", "chicken", "pasta", "rice", "avocado", "tofu", "curd", "chickpeas"];
  var hintIndex = 0;
  setInterval(function () {
    if (document.activeElement === $search[0] || $search.val()) return;
    hintIndex = (hintIndex + 1) % hints.length;
    $search.attr("placeholder", "Try " + hints[hintIndex] + "…");
  }, 2200);
});
