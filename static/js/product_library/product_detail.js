document.addEventListener('DOMContentLoaded', function () {
    document.documentElement.classList.add('js');

    /* ---------- pill tabs ---------- */
    var tabs = document.getElementById('dtabs');
    var panels = Array.prototype.slice.call(document.querySelectorAll('.tabpanel'));
    function select(name) {
        tabs.querySelectorAll('.tab').forEach(function (t) {
            var on = t.dataset.tab === name; t.classList.toggle('active', on); t.setAttribute('aria-selected', on);
        });
        panels.forEach(function (p) { p.hidden = p.dataset.panel !== name; });
        if (history.replaceState) history.replaceState(null, '', '#' + name);
    }
    if (tabs) {
        tabs.addEventListener('click', function (e) { var t = e.target.closest('.tab'); if (t) select(t.dataset.tab); });
        var start = location.hash.slice(1);
        select(panels.some(function (p) { return p.dataset.panel === start; }) ? start : 'overview');
    }

    /* ---------- animated progress ---------- */
    document.querySelectorAll('.meter__bar i').forEach(function (b) { setTimeout(function () { b.style.width = getComputedStyle(b).getPropertyValue('--w'); }, 250); });
    document.querySelectorAll('.ring-card .ring__fg').forEach(function (c) { setTimeout(function () { c.style.strokeDashoffset = 97.4 * (1 - (+c.dataset.pct || 0) / 100); }, 300); });

    /* ---------- dialogs ---------- */
    document.querySelectorAll('[data-open]').forEach(function (btn) {
        btn.addEventListener('click', function () { var d = document.getElementById(btn.dataset.open); if (d && d.showModal) d.showModal(); });
    });
    document.querySelectorAll('dialog [data-close]').forEach(function (btn) { btn.addEventListener('click', function () { btn.closest('dialog').close(); }); });
    document.querySelectorAll('dialog').forEach(function (d) { d.addEventListener('click', function (e) { if (e.target === d) d.close(); }); });
});
