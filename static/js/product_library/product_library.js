document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('filterForm');
    const category = document.getElementById('categoryFilter');
    if (!form) return;

    // Changing the category filters right away
    if (category) {
        category.addEventListener('change', function () {
            form.submit();
        });
    }
});
