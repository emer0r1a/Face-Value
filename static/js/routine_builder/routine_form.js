document.addEventListener('DOMContentLoaded', function () {
    var root = document.getElementById('rbForm');
    if (!root) return;

    function $(s, r) { return (r || document).querySelector(s); }
    function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
    function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text) n.textContent = text; return n; }
    var SVG = 'http://www.w3.org/2000/svg';
    function svgUse(id, cls, box) {
        var s = document.createElementNS(SVG, 'svg'); if (cls) s.setAttribute('class', cls);
        s.setAttribute('viewBox', box || '0 0 24 24');
        var u = document.createElementNS(SVG, 'use'); u.setAttribute('href', '#' + id); s.appendChild(u); return s;
    }
    function burstAt(node, n) {
        if (!(window.FV && FV.burst) || !node) return;
        var r = node.getBoundingClientRect(); FV.burst(r.left + r.width / 2, r.top + r.height / 2, n || 10);
    }

    var products = [], init = {};
    try { products = JSON.parse($('#rb-products').textContent); init = JSON.parse($('#rb-initial').textContent); } catch (e) {}
    var byId = {}; products.forEach(function (p, i) { p.tone = ['lime', 'sky', 'pink', 'sun', 'lav'][i % 5]; byId[p.id] = p; });

    var MAX = +root.dataset.maxSteps || 12;
    var state = {
        steps: (init.steps || []).filter(function (s) { return byId[s.product]; })
            .map(function (s) { return { pid: s.product, name: s.name || byId[s.product].step }; })
    };
    var DEFAULT_TIME = { morning: '07:00', afternoon: '13:00', evening: '20:00' };
    var timeTouched = !!(init.name || (init.steps && init.steps.length));
    var checked = {};        // preview ticks, by product id (never saved)

    var form = $('#builderForm');
    var nameIn = $('#rName'), timeIn = $('#rTime');
    var grid = $('#shelfGrid'), search = $('#shelfSearch');
    var list = $('#stepList'), drop = $('#stepDrop'), box = $('.stepsbox');
    var pvSteps = $('#pvSteps'), pvRoutine = $('#pvRoutine');
    var clientError = $('#clientError');

    function inSteps(pid) { return state.steps.some(function (s) { return s.pid === pid; }); }
    function artFor(p) {
        if (p.image) { var i = el('img'); i.src = p.image; i.alt = ''; return i; }
        return svgUse('a-' + p.art, 'art', '0 0 120 160');
    }
    function typeValue() { var r = $('input[name="routine_type"]:checked'); return r ? r.value : 'morning'; }
    function typeLabel() { var r = $('input[name="routine_type"]:checked'); return r ? $('b', r.closest('label')).textContent : 'Morning'; }

    /* ================= shelf ================= */
    var dragging = null;     // { kind: 'p'|'s', id|index }

    function renderShelf() {
        var q = search.value.trim().toLowerCase(), shown = 0;
        grid.textContent = '';
        products.forEach(function (p) {
            if (q && (p.name + ' ' + p.brand + ' ' + p.category).toLowerCase().indexOf(q) === -1) return;
            shown++;
            var added = inSteps(p.id);
            var t = el('div', 'ptile tone-' + p.tone + (added ? ' is-added' : '') + (p.archived ? ' is-archived' : ''));
            t.setAttribute('role', 'button'); t.tabIndex = 0; t.dataset.id = p.id;
            t.setAttribute('aria-label', (added ? 'Already added: ' : 'Add ') + p.name);
            t.draggable = !added;
            var img = el('span', 'ptile__img'); img.appendChild(artFor(p)); t.appendChild(img);
            t.appendChild(el('span', 'ptile__name', p.name));
            t.appendChild(el('small', '', p.brand));
            grid.appendChild(t);
        });
        if (!shown) grid.appendChild(el('p', 'shelfpick__none', products.length ? 'No products match that search.' : 'Nothing to add yet.'));
    }

    function addFromTile(t) {
        var id = +t.dataset.id; if (!id || inSteps(id)) return;
        if (addStep(id)) burstAt(t, 8);
    }
    grid.addEventListener('click', function (e) { var t = e.target.closest('.ptile'); if (t) addFromTile(t); });
    grid.addEventListener('keydown', function (e) {
        var t = e.target.closest('.ptile'); if (!t) return;
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); addFromTile(t); var again = $('.ptile[data-id="' + t.dataset.id + '"]', grid); if (again) again.focus(); }
    });
    grid.addEventListener('dragstart', function (e) {
        var t = e.target.closest('.ptile'); if (!t || t.classList.contains('is-added')) { e.preventDefault(); return; }
        dragging = { kind: 'p', id: +t.dataset.id };
        e.dataTransfer.effectAllowed = 'copy'; e.dataTransfer.setData('text/plain', 'p:' + t.dataset.id);
        t.classList.add('is-dragging');
    });
    grid.addEventListener('dragend', function () { dragging = null; $$('.ptile.is-dragging', grid).forEach(function (t) { t.classList.remove('is-dragging'); }); clearMarks(); });
    search.addEventListener('input', renderShelf);
    search.addEventListener('keydown', function (e) { if (e.key === 'Enter') e.preventDefault(); });

    /* ================= steps ================= */
    function addStep(pid, at) {
        if (state.steps.length >= MAX) { flash('A routine can have up to ' + MAX + ' steps.'); return false; }
        var p = byId[pid]; if (!p || inSteps(pid)) return false;
        var s = { pid: pid, name: p.step };
        if (typeof at === 'number') state.steps.splice(at, 0, s); else state.steps.push(s);
        hideError(); changed(); return true;
    }
    function removeStep(i) { var s = state.steps.splice(i, 1)[0]; if (s) delete checked[s.pid]; changed(); }
    function moveStep(from, to) {
        if (from === to || from < 0 || from >= state.steps.length) return;
        var s = state.steps.splice(from, 1)[0]; state.steps.splice(Math.max(0, Math.min(to, state.steps.length)), 0, s);
        changed();
    }

    function renderSteps(focusAt) {
        list.textContent = '';
        state.steps.forEach(function (s, i) {
            var p = byId[s.pid];
            var li = el('li', 'stepitem tone-' + p.tone); li.dataset.index = i;

            var hid = el('input'); hid.type = 'hidden'; hid.name = 'step_product'; hid.value = p.id; li.appendChild(hid);

            var grip = el('button', 'stepitem__grip', '⋮⋮'); grip.type = 'button'; grip.setAttribute('aria-label', 'Drag to reorder');
            grip.addEventListener('mousedown', function () { li.draggable = true; });
            grip.addEventListener('touchstart', function () { li.draggable = true; }, { passive: true });
            li.appendChild(grip);

            li.appendChild(el('span', 'stepitem__n', String(i + 1)));
            var th = el('span', 'stepitem__thumb'); th.appendChild(artFor(p)); li.appendChild(th);

            var body = el('div', 'stepitem__body');
            var inp = el('input', 'stepitem__name'); inp.type = 'text'; inp.name = 'step_name'; inp.maxLength = 50; inp.value = s.name;
            inp.setAttribute('aria-label', 'Step name for ' + p.name);
            inp.addEventListener('input', function () { s.name = inp.value; renderPreview(); });
            inp.addEventListener('keydown', function (e) { if (e.key === 'Enter') e.preventDefault(); });
            body.appendChild(inp); body.appendChild(el('span', 'stepitem__prod', p.name + (p.archived ? ' (archived)' : '')));
            li.appendChild(body);

            var ctrl = el('div', 'stepitem__ctrl');
            var up = el('button', 'mini mini--up'); up.type = 'button'; up.setAttribute('aria-label', 'Move up'); up.disabled = i === 0; up.appendChild(svgUse('ic-arrow-l'));
            var dn = el('button', 'mini mini--down'); dn.type = 'button'; dn.setAttribute('aria-label', 'Move down'); dn.disabled = i === state.steps.length - 1; dn.appendChild(svgUse('ic-arrow-l'));
            var rm = el('button', 'mini mini--x', '×'); rm.type = 'button'; rm.setAttribute('aria-label', 'Remove ' + p.name);
            up.addEventListener('click', function () { focusStep(i - 1, '.mini--up'); moveStep(i, i - 1); });
            dn.addEventListener('click', function () { focusStep(i + 1, '.mini--down'); moveStep(i, i + 1); });
            rm.addEventListener('click', function () { removeStep(i); });
            ctrl.appendChild(up); ctrl.appendChild(dn); ctrl.appendChild(rm); li.appendChild(ctrl);

            li.addEventListener('dragstart', function (e) {
                dragging = { kind: 's', index: i };
                e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', 's:' + i);
                li.classList.add('is-dragging');
            });
            li.addEventListener('dragend', function () { li.draggable = false; li.classList.remove('is-dragging'); dragging = null; clearMarks(); });
            list.appendChild(li);
        });
        var n = state.steps.length;
        $('#stepCount').textContent = n + (n === MAX ? ' / ' + MAX : '') + ' step' + (n === 1 ? '' : 's');
        $('span', drop).textContent = n ? 'Drop here to add to the end' : 'Drop a product here';
        if (focusAt) { var b = $('.stepitem[data-index="' + focusAt.i + '"] ' + focusAt.sel); if (b && !b.disabled) b.focus(); }
    }
    var pendingFocus = null;
    function focusStep(i, sel) { pendingFocus = { i: i, sel: sel }; }

    /* drag targets */
    function clearMarks() {
        $$('.drop-before, .drop-after', list).forEach(function (n) { n.classList.remove('drop-before', 'drop-after'); });
        drop.classList.remove('drag');
    }
    function indexAt(y) {
        var items = $$('.stepitem', list);
        for (var i = 0; i < items.length; i++) {
            var r = items[i].getBoundingClientRect();
            if (y < r.top + r.height / 2) return i;
        }
        return items.length;
    }
    box.addEventListener('dragover', function (e) {
        if (!dragging) return;
        e.preventDefault(); e.dataTransfer.dropEffect = dragging.kind === 'p' ? 'copy' : 'move';
        clearMarks(); drop.classList.add('drag');
        var items = $$('.stepitem', list), at = indexAt(e.clientY);
        if (!items.length) return;
        if (at < items.length) items[at].classList.add('drop-before'); else items[items.length - 1].classList.add('drop-after');
    });
    box.addEventListener('dragleave', function (e) { if (!box.contains(e.relatedTarget)) clearMarks(); });
    box.addEventListener('drop', function (e) {
        if (!dragging) return; e.preventDefault();
        var at = indexAt(e.clientY), d = dragging; clearMarks(); dragging = null;
        if (d.kind === 'p') { if (addStep(d.id, at)) { var li = $('.stepitem[data-index="' + at + '"]'); if (li) burstAt(li, 8); } }
        else { moveStep(d.index, at > d.index ? at - 1 : at); }
    });

    /* ================= preview ================= */
    function fmtTime(v) {
        var m = /^(\d{1,2}):(\d{2})/.exec(v || ''); if (!m) return 'Pick a time';
        var h = +m[1], ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + m[2] + ' ' + ap;
    }
    function paintLeaf() {
        var n = state.steps.length, c = state.steps.filter(function (s) { return checked[s.pid]; }).length;
        var pct = n ? Math.round(100 * c / n) : 0;
        $('.leafbar i', pvRoutine).style.width = pct + '%';
        $('.leafbar .leaf', pvRoutine).style.left = pct + '%';
        $('#pvPct').textContent = pct + '%';
        pvRoutine.classList.toggle('is-done', n > 0 && c === n);
    }
    function renderPreview() {
        $('#pvName').textContent = nameIn.value.trim() || 'Your routine';
        $('#pvType').textContent = typeLabel();
        pvSteps.textContent = '';
        state.steps.forEach(function (s) {
            var p = byId[s.pid], li = el('li'), lab = el('label', 'check');
            var cb = el('input'); cb.type = 'checkbox'; cb.checked = !!checked[s.pid]; cb.dataset.pid = s.pid;
            var bx = el('span', 'check__box'); bx.appendChild(svgUse('ic-check'));
            var th = el('span', 'check__thumb tone-' + p.tone); th.appendChild(artFor(p));
            var tx = el('span', 'check__text'); tx.appendChild(el('b', '', s.name || p.step)); tx.appendChild(el('em', '', p.name));
            lab.appendChild(cb); lab.appendChild(bx); lab.appendChild(th); lab.appendChild(tx);
            li.appendChild(lab); pvSteps.appendChild(li);
        });
        $('#pvEmpty').hidden = state.steps.length > 0;

        var days = $('#pvDays'); days.textContent = '';
        $$('input[name="days"]').forEach(function (d) {
            var s = el('span', 'rdays__d' + (d.checked ? ' on' : ''), d.nextElementSibling.textContent.charAt(0));
            s.title = d.nextElementSibling.title; days.appendChild(s);
        });
        var t = $('#pvTime'); t.textContent = ''; t.appendChild(svgUse('ic-clock')); t.appendChild(document.createTextNode(fmtTime(timeIn.value)));
        paintLeaf();
    }
    pvSteps.addEventListener('change', function (e) {
        var cb = e.target; if (!cb.dataset.pid) return;
        var was = pvRoutine.classList.contains('is-done');
        checked[cb.dataset.pid] = cb.checked; paintLeaf();
        if (!was && pvRoutine.classList.contains('is-done')) burstAt(cb.nextElementSibling, 14);
    });

    /* ================= clash check ================= */
    var clashBox = $('#clashBox'), clashTimer = null, clashToken = 0, clashUrl = root.dataset.clashUrl;
    var sevIcon = { high: '⚠️', moderate: '🌦️', medium: '🌦️', low: '🌤️' };
    function badge(kind, icon, title, text, tip) {
        var b = el('div', 'badge badge--' + kind); b.appendChild(el('span', 'badge__icon', icon));
        var body = el('div'); body.appendChild(el('strong', '', title)); body.appendChild(el('p', '', text));
        if (tip) body.appendChild(el('p', 'tip', '💡 ' + tip));
        b.appendChild(body); return b;
    }
    function checkClashes() {
        clearTimeout(clashTimer);
        var ids = state.steps.map(function (s) { return s.pid; });
        if (ids.length < 2) { clashToken++; clashBox.textContent = ''; return; }
        var token = ++clashToken;
        clashTimer = setTimeout(function () {
            fetch(clashUrl + '?ids=' + ids.join(','), { credentials: 'same-origin' })
                .then(function (r) { if (!r.ok) throw new Error(); return r.json(); })
                .then(function (d) {
                    if (token !== clashToken) return;
                    clashBox.textContent = '';
                    var missing = d.checked - d.with_ingredients;
                    if (d.clashes.length) {
                        d.clashes.forEach(function (c) {
                            var sev = sevIcon[c.severity] ? c.severity : 'moderate';
                            clashBox.appendChild(badge(sev, sevIcon[sev], c.pair, c.products[0] + ' and ' + c.products[1] + '. ' + c.message, c.tip));
                        });
                    } else if (d.with_ingredients < 2) {
                        clashBox.appendChild(badge('info', '📝', 'Nothing to compare yet', 'Add ingredient lists to these products and we can check how they layer.'));
                    } else if (missing > 0) {
                        clashBox.appendChild(badge('info', '📝', 'Partly checked', missing + ' product' + (missing === 1 ? ' has' : 's have') + ' no ingredients saved, so ' + (missing === 1 ? 'it was' : 'they were') + ' skipped. No clashes found in the rest.'));
                    } else {
                        clashBox.appendChild(badge('ok', '✅', 'No known clashes', "We didn't find a flagged interaction in this routine. That only covers combinations we know about."));
                    }
                })
                .catch(function () { if (token === clashToken) { clashBox.textContent = ''; clashBox.appendChild(badge('info', '☁️', "Couldn't check right now", 'The clash check will run again when you change a step.')); } });
        }, 280);
    }

    /* ================= basics + days ================= */
    function showError(msg) { clientError.textContent = msg; clientError.hidden = false; var s = $('#serverError'); if (s) s.hidden = true; clientError.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
    function hideError() { clientError.hidden = true; }
    var flashTimer = null;
    function flash(msg) { showError(msg); clearTimeout(flashTimer); flashTimer = setTimeout(hideError, 3500); }

    nameIn.addEventListener('input', function () { renderPreview(); });
    nameIn.addEventListener('keydown', function (e) { if (e.key === 'Enter') e.preventDefault(); });
    $$('input[name="routine_type"]').forEach(function (r) {
        r.addEventListener('change', function () {
            if (!timeTouched) timeIn.value = DEFAULT_TIME[typeValue()] || timeIn.value;
            renderPreview();
        });
    });
    $$('input[name="days"]').forEach(function (d) { d.addEventListener('change', renderPreview); });
    timeIn.addEventListener('input', function () { timeTouched = true; renderPreview(); });

    var groups = { all: ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'], weekdays: ['mon', 'tue', 'wed', 'thu', 'fri'], weekend: ['sat', 'sun'], none: [] };
    $$('.quick .pill').forEach(function (b) {
        b.addEventListener('click', function () {
            var set = groups[b.dataset.days] || [];
            $$('input[name="days"]').forEach(function (d) { d.checked = set.indexOf(d.value) !== -1; });
            renderPreview();
        });
    });

    /* ================= submit ================= */
    var submitting = false;
    window.addEventListener('pageshow', function () { submitting = false; });
    form.addEventListener('submit', function (e) {
        var msg = '';
        if (!nameIn.value.trim()) { msg = 'Give your routine a name.'; nameIn.focus(); }
        else if (!state.steps.length) msg = 'Add at least one product to your routine.';
        else if (!$$('input[name="days"]:checked').length) msg = 'Pick at least one day.';
        else if (!timeIn.value) { msg = 'Choose a time for your reminder.'; timeIn.focus(); }
        if (msg || submitting) { e.preventDefault(); if (msg) showError(msg); return; }
        submitting = true;
    });

    /* ================= go ================= */
    function changed() {
        renderShelf(); renderSteps(pendingFocus); pendingFocus = null; renderPreview(); checkClashes();
    }
    // (typing in a step name only repaints the preview)
    changed();
});
