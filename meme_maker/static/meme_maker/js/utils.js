/* Meme Maker Utilities */
function updateSort(value) {
    var url = new URL(window.location);
    url.searchParams.set('order', value);
    window.location = url;
}

function updatePerPage(value) {
    var url = new URL(window.location);
    url.searchParams.set('per_page', value);
    url.searchParams.set('page', 1);
    window.location = url;
}
