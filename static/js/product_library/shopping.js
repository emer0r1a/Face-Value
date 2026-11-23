(function () {
    'use strict';
    var btn = document.getElementById('copyList');
    if (!btn) return;
    btn.addEventListener('click', function () {
        var out = [];
        document.querySelectorAll('.shop-card[data-list]').forEach(function (sec) {
            var lines = [];
            sec.querySelectorAll('[data-line]').forEach(function (li) { lines.push('- ' + li.dataset.line); });
            if (lines.length) out.push(sec.dataset.list + ':\n' + lines.join('\n'));
        });
        var text = out.join('\n\n');
        var done = function () { var old = btn.textContent; btn.textContent = 'Copied!'; setTimeout(function () { btn.textContent = old; }, 1800); };
        if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, function () { window.prompt('Copy your list:', text); });
        else window.prompt('Copy your list:', text);
    });
})();
