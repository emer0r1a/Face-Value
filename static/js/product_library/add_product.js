document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('addProductForm');
    const ingredients = document.getElementById('ingredients');
    const counter = document.getElementById('ingredientCount');
    const preview = document.getElementById('ingredientPreview');
    const submitBtn = document.getElementById('submitBtn');
    if (!form) return;

    // Same parsing rules as the server: split on commas/new lines, drop duplicates
    function parseIngredients() {
        const seen = new Set();
        const names = [];
        ingredients.value.split(/[,\n]/).forEach(function (part) {
            const name = part.trim().replace(/\s+/g, ' ');
            const key = name.toLowerCase();
            if (name && !seen.has(key)) {
                seen.add(key);
                names.push(name);
            }
        });
        return names;
    }

    let shown = [];

    function update() {
        const names = parseIngredients();
        counter.textContent = names.length + (names.length === 1 ? ' ingredient' : ' ingredients');

        // Only rebuild the chips when the list changed, so new ones pop in
        if (names.join('|') === shown.join('|')) return;
        shown = names;
        preview.innerHTML = '';
        names.forEach(function (name) {
            const chip = document.createElement('span');
            chip.className = 'chip';
            chip.textContent = name;
            preview.appendChild(chip);
        });
    }

    ingredients.addEventListener('input', update);
    update();

    form.addEventListener('submit', function (e) {
        const required = ['product_name', 'brand'];
        for (const id of required) {
            const field = document.getElementById(id);
            if (!field.value.trim()) {
                e.preventDefault();
                alert('Please fill in the product name and brand.');
                field.focus();
                return;
            }
        }

        // Prevent double submissions
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving...';
    });
});
