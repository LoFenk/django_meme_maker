/* Imgflip search integration */
(function() {
    'use strict';

    function $(selector, root) {
        return (root || document).querySelector(selector);
    }

    function setActive(tabTarget, tabsRoot, panelsRoot) {
        if (!tabsRoot || !panelsRoot) return;
        tabsRoot.querySelectorAll('.meme-tab').forEach(function(tab) {
            tab.classList.toggle('is-active', tab.dataset.tabTarget === tabTarget);
        });
        panelsRoot.querySelectorAll('.meme-tab-panel').forEach(function(panel) {
            panel.classList.toggle('is-active', panel.dataset.tabPanel === tabTarget);
        });
    }

    function initImgflipSearch() {
        var tabsRoot = $('[data-imgflip-tabs]');
        var panelsRoot = $('[data-imgflip-panels]');
        var imgflipTab = $('[data-imgflip-tab]');
        var imgflipPanel = $('[data-tab-panel="imgflip"]');
        var localTab = $('[data-tab-target="local"]');
        var queryInput = $('[data-imgflip-query]');

        if (!imgflipTab || !imgflipPanel || !tabsRoot || !panelsRoot) {
            return;
        }

        var resultsEl = $('[data-imgflip-results]', imgflipPanel);
        var loadingEl = $('[data-imgflip-loading]', imgflipPanel);
        var isLoading = false;
        var loadedQuery = null;

        function setLoading(state) {
            isLoading = state;
            if (loadingEl) loadingEl.hidden = !state;
        }

        function loadResults() {
            if (!resultsEl || isLoading) return;
            var url = imgflipTab.dataset.imgflipUrl;
            if (!url) return;
            var query = queryInput ? queryInput.value : '';
            if (loadedQuery === query && resultsEl.dataset.loaded === '1') {
                return;
            }
            setLoading(true);
            fetch(url + '?q=' + encodeURIComponent(query), {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
                .then(function(resp) { return resp.text(); })
                .then(function(html) {
                    resultsEl.innerHTML = html;
                    resultsEl.dataset.loaded = '1';
                    loadedQuery = query;
                })
                .catch(function() {
                    resultsEl.innerHTML = '<div class="imgflip-empty"><p>Unable to load Imgflip results.</p></div>';
                })
                .finally(function() {
                    setLoading(false);
                });
        }

        imgflipTab.addEventListener('click', function(event) {
            event.preventDefault();
            if (imgflipTab.dataset.imgflipDisabled === '1') {
                return;
            }
            setActive('imgflip', tabsRoot, panelsRoot);
            loadResults();
        });

        if (localTab) {
            localTab.addEventListener('click', function(event) {
                event.preventDefault();
                setActive('local', tabsRoot, panelsRoot);
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initImgflipSearch);
    } else {
        initImgflipSearch();
    }
})();
