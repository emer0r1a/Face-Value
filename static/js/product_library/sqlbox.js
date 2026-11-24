document.addEventListener('DOMContentLoaded', function () {
    var KEYWORDS = /^(SELECT|FROM|INNER JOIN|LEFT OUTER JOIN|ON|WHERE|AND|OR|NOT|IN|ORDER BY|GROUP BY|ASC|DESC|LIKE|UPPER|AS|DISTINCT|IS|NULL)$/;
    var TOKEN = /("[^"]*"|'[^']*'|\b\d+\b|\bINNER JOIN\b|\bLEFT OUTER JOIN\b|\bORDER BY\b|\bGROUP BY\b|\b[A-Z]{2,}\b)/g;

    // colour the SQL without ever inserting HTML (text nodes + spans only)
    function highlight(pre) {
        var text = pre.textContent; pre.textContent = '';
        var last = 0, m;
        TOKEN.lastIndex = 0;
        while ((m = TOKEN.exec(text))) {
            if (m.index > last) pre.appendChild(document.createTextNode(text.slice(last, m.index)));
            var t = m[0], cls = null;
            if (t.charAt(0) === '"') cls = 'sq-id';
            else if (t.charAt(0) === "'") cls = 'sq-str';
            else if (/^\d+$/.test(t)) cls = 'sq-num';
            else if (KEYWORDS.test(t)) cls = 'sq-kw';
            if (cls) { var s = document.createElement('span'); s.className = cls; s.textContent = t; pre.appendChild(s); }
            else pre.appendChild(document.createTextNode(t));
            last = m.index + t.length;
        }
        if (last < text.length) pre.appendChild(document.createTextNode(text.slice(last)));
    }

    document.querySelectorAll('[data-sqlbox]').forEach(function (box) {
        var plain = {};
        box.querySelectorAll('pre.sqlcode').forEach(function (pre) { plain[pre.dataset.view] = pre.textContent; highlight(pre); });
        var current = 'short';

        box.querySelectorAll('.tab').forEach(function (tab) {
            tab.addEventListener('click', function () {
                current = tab.dataset.view;
                box.querySelectorAll('.tab').forEach(function (t) { t.classList.toggle('active', t === tab); t.setAttribute('aria-selected', t === tab); });
                box.querySelectorAll('pre.sqlcode').forEach(function (p) { p.hidden = p.dataset.view !== current; });
            });
        });

        var copy = box.querySelector('[data-copy]');
        copy.addEventListener('click', function () {
            // always copy the full, runnable statement
            var done = function () { copy.textContent = 'Copied ✓'; setTimeout(function () { copy.textContent = 'Copy'; }, 1500); };
            if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(plain.full).then(done, function () { copy.textContent = 'Press Ctrl+C'; });
            else { var r = document.createRange(); var pre = box.querySelector('pre[data-view="full"]'); pre.hidden = false; r.selectNodeContents(pre); var sel = getSelection(); sel.removeAllRanges(); sel.addRange(r); try { document.execCommand('copy'); done(); } catch (e) {} pre.hidden = current !== 'full'; }
        });
    });
});
