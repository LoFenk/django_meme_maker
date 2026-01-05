/* Meme Maker Rating Widget */
(function() {
    'use strict';

    function getCSRFToken() {
        var name = 'csrftoken';
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var c = cookies[i].trim();
            if (c.indexOf(name + '=') === 0) {
                return decodeURIComponent(c.substring(name.length + 1));
            }
        }
        var input = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return input ? input.value : null;
    }

    function updateStarDisplay(container, avgRating) {
        if (!container) return;
        var stars = container.querySelectorAll('.star');
        var rounded = Math.round(avgRating);
        stars.forEach(function(star, i) {
            star.textContent = i < rounded ? '★' : '☆';
            star.classList.toggle('empty', i >= rounded);
        });
    }

    function initRatingWidgets() {
        document.querySelectorAll('[data-rating-widget]').forEach(function(widget) {
            var ratingInput = widget.querySelector('[data-rating-input]');
            if (!ratingInput) return;

            var labels = ratingInput.querySelectorAll('label');
            var ratingDisplay = widget.querySelector('[data-rating-display]');
            var ratingText = widget.querySelector('[data-rating-text]');
            var rateUrl = widget.dataset.rateUrl;

            labels.forEach(function(label) {
                label.addEventListener('click', function(e) {
                    e.preventDefault();
                    var stars = parseInt(this.dataset.value);
                    
                    // Immediate visual feedback
                    var radio = widget.querySelector('input[value="' + stars + '"]');
                    if (radio) {
                        radio.checked = true;
                        radio.dispatchEvent(new Event('change'));
                    }

                    fetch(rateUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCSRFToken()
                        },
                        body: JSON.stringify({ stars: stars })
                    })
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.success) {
                            updateStarDisplay(ratingDisplay, data.average_rating);
                            if (ratingText) ratingText.textContent = data.rating_display;
                        }
                    })
                    .catch(function(err) { console.error('Rating failed:', err); });
                });
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initRatingWidgets);
    } else {
        initRatingWidgets();
    }
})();

