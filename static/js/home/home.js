document.addEventListener('DOMContentLoaded', function () {
    const FV = window.FV;
    const products = FV.store.getProducts();
    const settings = FV.store.getSettings();

    const brands = new Set();
    const categories = new Set();
    let ingredientTotal = 0;
    products.forEach(function (p) {
        brands.add(p.brand.toLowerCase());
        categories.add(p.category);
        ingredientTotal += p.ingredients.length;
    });

    const values = { products: products.length, ingredients: ingredientTotal, brands: brands.size, categories: categories.size };
    document.querySelectorAll('[data-stat]').forEach(function (el) {
        const target = values[el.dataset.stat] || 0;
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || target === 0) {
            el.textContent = target;
            return;
        }
        const start = performance.now();
        function tick(now) {
            const t = Math.min((now - start) / 700, 1);
            el.textContent = Math.round(target * (1 - Math.pow(1 - t, 3)));
            if (t < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    });

    const greeting = document.getElementById('welcomeName');
    if (greeting && settings.name.trim()) greeting.textContent = settings.name.trim().split(' ')[0];

    const recent = document.getElementById('recentList');
    const recentEmpty = document.getElementById('recentEmpty');
    if (!recent) return;
    const latest = products.slice().sort(function (a, b) { return new Date(b.added) - new Date(a.added); }).slice(0, 3);
    recent.hidden = latest.length === 0;
    if (recentEmpty) recentEmpty.hidden = latest.length > 0;

    latest.forEach(function (p, i) {
        const li = document.createElement('li');
        li.className = 'recent__item ' + FV.cardColor(i);

        const letter = document.createElement('span');
        letter.className = 'recent__letter';
        letter.textContent = p.name.charAt(0).toUpperCase();

        const body = document.createElement('div');
        body.className = 'recent__body';
        const title = document.createElement('strong');
        title.textContent = p.name;
        const meta = document.createElement('span');
        meta.textContent = p.brand + ' · ' + p.category + ' · ' + FV.formatDate(p.added);
        body.append(title, meta);

        const tag = document.createElement('span');
        tag.className = 'chip';
        tag.textContent = FV.plural(p.ingredients.length, 'ingredient');

        li.append(letter, body, tag);
        recent.appendChild(li);
    });
});
