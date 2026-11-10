document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('addProductForm');
    const ingredients = document.getElementById('ingredients');
    const counter = document.getElementById('ingredientCount');
    const submitBtn = document.getElementById('submitBtn');
    if (!form) return;

    // Same parsing rules as the server: split on commas/new lines, drop duplicates
    function countIngredients() {
        const seen = new Set();
        ingredients.value.split(/[,\n]/).forEach(function (part) {
            const name = part.trim().replace(/\s+/g, ' ').toLowerCase();
            if (name) seen.add(name);
        });
        const n = seen.size;
        counter.textContent = n + (n === 1 ? ' ingredient' : ' ingredients');
    }

    ingredients.addEventListener('input', countIngredients);
    countIngredients();

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
