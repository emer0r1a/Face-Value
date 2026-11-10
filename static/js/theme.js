(function () {
    try {
        var settings = JSON.parse(localStorage.getItem('fv-settings') || '{}');
        if (settings.darkMode) document.documentElement.setAttribute('data-theme', 'dark');
    } catch (err) {}
})();
