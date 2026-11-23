(function () {
    try {
        var root = document.documentElement;
        // Signed-in pages carry the saved preference from the server; keep
        // the browser copy in step so login/landing pages match too.
        if (root.hasAttribute('data-user-theme')) {
            var dark = root.getAttribute('data-theme') === 'dark';
            var s = JSON.parse(localStorage.getItem('fv-settings') || '{}');
            s.darkMode = dark;
            localStorage.setItem('fv-settings', JSON.stringify(s));
            return;
        }
        var settings = JSON.parse(localStorage.getItem('fv-settings') || '{}');
        if (settings.darkMode) root.setAttribute('data-theme', 'dark');
    } catch (err) {}
})();
