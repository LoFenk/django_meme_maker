/* Meme Maker Utilities */
function updateSort(value) {
    var url = new URL(window.location);
    url.searchParams.set('order', value);
    window.location = url;
}

