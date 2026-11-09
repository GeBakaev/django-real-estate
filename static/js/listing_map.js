// Map of all listings: markers from the JSON the view embeds, popups with a card.
(function () {
  var el = document.getElementById("listing-map");
  var data = document.getElementById("listing-map-data");
  if (!el || !data || typeof L === "undefined") return;

  var markers = JSON.parse(data.textContent);

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (char) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
    });
  }

  var map = L.map(el, { scrollWheelZoom: false });
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  var group = L.featureGroup();
  markers.forEach(function (item) {
    var html =
      '<a href="' + escapeHtml(item.url) + '" class="map-popup">' +
      (item.image ? '<img src="' + escapeHtml(item.image) + '" alt="" width="320" height="240">' : "") +
      "<strong>" + escapeHtml(item.title) + "</strong>" +
      "<span>" + escapeHtml(item.location) + " · " + escapeHtml(item.kind) + "</span>" +
      "<em>" + escapeHtml(item.price) + "</em>" +
      "</a>";
    L.marker([item.lat, item.lng], { title: item.title })
      .bindPopup(html, { minWidth: 220, maxWidth: 240 })
      .addTo(group);
  });
  group.addTo(map);
  map.fitBounds(group.getBounds().pad(0.15), { maxZoom: 14 });
})();
