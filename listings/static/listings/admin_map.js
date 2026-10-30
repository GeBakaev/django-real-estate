// Leaflet coordinate picker for the Listing admin form.
// Keeps #id_latitude / #id_longitude in sync with a draggable marker.
(function () {
  "use strict";

  var DEFAULT_CENTER = [33.8938, 35.5018]; // Beirut
  var DEFAULT_ZOOM = 8;
  var PICKED_ZOOM = 14;

  function parse(input) {
    var value = parseFloat(input.value);
    return isNaN(value) ? null : value;
  }

  function init() {
    var latInput = document.getElementById("id_latitude");
    var lngInput = document.getElementById("id_longitude");
    if (!latInput || !lngInput || typeof L === "undefined") {
      return;
    }

    var container = document.createElement("div");
    container.id = "listing-map";
    container.style.height = "360px";
    container.style.maxWidth = "760px";
    container.style.margin = "10px 0";
    container.style.border = "1px solid var(--border-color, #ccc)";
    lngInput.closest(".form-row, .fieldBox, div").insertAdjacentElement("afterend", container);

    var lat = parse(latInput);
    var lng = parse(lngInput);
    var hasPoint = lat !== null && lng !== null;

    var map = L.map(container).setView(hasPoint ? [lat, lng] : DEFAULT_CENTER, hasPoint ? PICKED_ZOOM : DEFAULT_ZOOM);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    var marker = null;

    function setPoint(latlng, pan) {
      latInput.value = latlng.lat.toFixed(6);
      lngInput.value = latlng.lng.toFixed(6);
      if (marker) {
        marker.setLatLng(latlng);
      } else {
        marker = L.marker(latlng, { draggable: true }).addTo(map);
        marker.on("dragend", function () {
          setPoint(marker.getLatLng(), false);
        });
      }
      if (pan) {
        map.setView(latlng, Math.max(map.getZoom(), PICKED_ZOOM));
      }
    }

    if (hasPoint) {
      setPoint(L.latLng(lat, lng), false);
    }

    map.on("click", function (e) {
      setPoint(e.latlng, false);
    });

    function syncFromInputs() {
      var a = parse(latInput);
      var b = parse(lngInput);
      if (a !== null && b !== null) {
        setPoint(L.latLng(a, b), true);
      }
    }
    latInput.addEventListener("change", syncFromInputs);
    lngInput.addEventListener("change", syncFromInputs);

    // The map is created inside a collapsed/laid-out fieldset; make sure tiles size correctly.
    setTimeout(function () {
      map.invalidateSize();
    }, 0);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
