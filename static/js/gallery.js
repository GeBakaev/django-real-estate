// Photo gallery on the listing detail page: thumbnails, arrows, keyboard and swipe.
(function () {
    document.querySelectorAll("[data-gallery]").forEach(function (gallery) {
        var main = gallery.querySelector("[data-gallery-main]");
        var thumbs = Array.prototype.slice.call(gallery.querySelectorAll("[data-gallery-thumb]"));
        var counter = gallery.querySelector("[data-gallery-counter]");
        if (!main || thumbs.length < 2) return;

        var index = 0;

        function show(i) {
            index = (i + thumbs.length) % thumbs.length;
            var thumb = thumbs[index];
            main.src = thumb.dataset.src;
            main.alt = thumb.dataset.alt || "";
            thumbs.forEach(function (t, n) {
                if (n === index) t.setAttribute("data-active", "");
                else t.removeAttribute("data-active");
            });
            if (counter) counter.textContent = (index + 1) + " / " + thumbs.length;
        }

        thumbs.forEach(function (thumb, n) {
            thumb.addEventListener("click", function () { show(n); });
        });
        var prev = gallery.querySelector("[data-gallery-prev]");
        var next = gallery.querySelector("[data-gallery-next]");
        if (prev) prev.addEventListener("click", function () { show(index - 1); });
        if (next) next.addEventListener("click", function () { show(index + 1); });

        gallery.addEventListener("keydown", function (event) {
            if (event.key === "ArrowLeft") { show(index - 1); event.preventDefault(); }
            else if (event.key === "ArrowRight") { show(index + 1); event.preventDefault(); }
        });

        var startX = null;
        main.addEventListener("touchstart", function (event) {
            startX = event.touches[0].clientX;
        }, { passive: true });
        main.addEventListener("touchend", function (event) {
            if (startX === null) return;
            var dx = event.changedTouches[0].clientX - startX;
            if (Math.abs(dx) > 40) show(dx < 0 ? index + 1 : index - 1);
            startX = null;
        });
    });
})();
