// Armoseal Insulation — small helpers. The site works without this file;
// it only adds the phone menu button and the quote form email helper.

(function () {
  // Mobile menu
  var toggle = document.querySelector(".menu-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.querySelector(".menu-label").textContent = open ? "Close" : "Menu";
    });
  }

  // Footer year
  var year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();

  // Quote form: opens the visitor's email app with their details filled in.
  // When the site goes online this can be swapped for a form service
  // (e.g. Formspree or Netlify Forms) so requests arrive without an email app.
  var form = document.getElementById("quote-form");
  if (form) {
    // Preselect a service when arriving from a "Request a Quote" button
    var wanted = new URLSearchParams(window.location.search).get("service");
    var select = form.querySelector("#service");
    if (wanted && select) {
      Array.prototype.forEach.call(select.options, function (o) {
        if (o.text === wanted) select.value = o.value;
      });
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var data = new FormData(form);
      var lines = [
        "Name: " + (data.get("name") || ""),
        "Phone: " + (data.get("phone") || ""),
        "Email: " + (data.get("email") || ""),
        "Service: " + (data.get("service") || ""),
        "Best time to call: " + (data.get("time") || ""),
        "",
        "About my project:",
        data.get("message") || ""
      ];
      var subject = "Quote request from " + (data.get("name") || "website visitor");
      window.location.href =
        "mailto:armosealinsulation@gmail.com" +
        "?subject=" + encodeURIComponent(subject) +
        "&body=" + encodeURIComponent(lines.join("\n"));
    });
  }
})();
