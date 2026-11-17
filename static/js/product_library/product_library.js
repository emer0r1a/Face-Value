document.addEventListener('DOMContentLoaded', function () {
    var grid = document.getElementById('grid');
    var tools = document.getElementById('libTools');
    if (!tools) return;

    var input = document.getElementById('searchInput');
    var sort = document.getElementById('sortSelect');
    var pills = document.getElementById('pills');
    var count = document.getElementById('resultCount');
    var empty = document.getElementById('emptyState');
    var form = document.getElementById('filterForm');
    var cards = grid ? Array.prototype.slice.call(grid.children) : [];
    var total = cards.length;
    var cat = tools.dataset.initialCat || '';

    // The server already filtered on ?q / ?category, but once JS is running
    // every card is on the page, so filter live instead of reloading.
    form.addEventListener('submit', function (e) { e.preventDefault(); });

    function apply() {
        var q = input.value.trim().toLowerCase();
        var words = q.split(/\s+/).filter(Boolean);
        var shown = 0;

        cards.forEach(function (c) {
            var okCat = !cat || c.dataset.cat.toLowerCase() === cat.toLowerCase();
            var okQ = words.every(function (w) { return c.dataset.search.indexOf(w) !== -1; });
            var show = okCat && okQ;
            c.hidden = !show;
            if (show) shown++;
        });

        if (count) count.textContent = 'Showing ' + shown + ' of ' + total + ' product' + (total === 1 ? '' : 's');
        if (empty && total) empty.hidden = shown !== 0;

        // keep the URL shareable without reloading
        var params = new URLSearchParams();
        if (q) params.set('q', input.value.trim());
        if (cat) params.set('category', cat);
        var qs = params.toString();
        history.replaceState(null, '', location.pathname + (qs ? '?' + qs : ''));
    }

    function reorder() {
        var key = sort.value;
        var sorted = cards.slice().sort(function (a, b) {
            if (key === 'name') return a.dataset.name.localeCompare(b.dataset.name);
            if (key === 'brand') return a.dataset.brand.localeCompare(b.dataset.brand) || a.dataset.name.localeCompare(b.dataset.name);
            return (+b.dataset.added) - (+a.dataset.added);
        });
        sorted.forEach(function (c) { grid.appendChild(c); });
    }

    function setCat(value) {
        cat = value;
        if (pills) pills.querySelectorAll('.pill').forEach(function (p) {
            p.classList.toggle('active', p.dataset.cat.toLowerCase() === value.toLowerCase());
        });
        apply();
    }

    if (input) input.addEventListener('input', apply);
    if (sort && grid) sort.addEventListener('change', reorder);
    if (pills) pills.addEventListener('click', function (e) {
        var p = e.target.closest('.pill');
        if (p) setCat(p.dataset.cat);
    });
    var clear = document.getElementById('clearFilters');
    if (clear) clear.addEventListener('click', function () { input.value = ''; setCat(''); input.focus(); });

    apply();
});
