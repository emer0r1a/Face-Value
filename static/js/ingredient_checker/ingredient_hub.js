document.addEventListener('DOMContentLoaded', function () {
    var root = document.getElementById('ih');
    if (!root) return;

    function $(s, r) { return (r || document).querySelector(s); }
    function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
    function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text != null && text !== '') n.textContent = text; return n; }
    var SVG = 'http://www.w3.org/2000/svg';
    function art(p) {
        if (p.image) { var i = el('img'); i.src = p.image; i.alt = ''; return i; }
        var s = document.createElementNS(SVG, 'svg'); s.setAttribute('class', 'art'); s.setAttribute('viewBox', '0 0 120 160');
        var u = document.createElementNS(SVG, 'use'); u.setAttribute('href', '#a-' + p.art); s.appendChild(u); return s;
    }
    function burstAt(node, n) {
        if (!(window.FV && FV.burst) || !node) return;
        var r = node.getBoundingClientRect(); FV.burst(r.left + r.width / 2, r.top + r.height / 2, n || 10);
    }
    function onActivate(node, fn) {
        node.addEventListener('click', fn);
        node.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fn(e); } });
    }

    /* ---------------- data ---------------- */
    var data = { ingredients: [], interactions: [], groups: [], products: [], routines: [] };
    try { data = JSON.parse($('#hub-data').textContent); } catch (e) {}

    var ingById = {}, prodById = {}, groupBy = {}, TONES = ['lime', 'sky', 'pink', 'sun', 'lav'];
    data.ingredients.forEach(function (i) { ingById[i.id] = i; });
    data.products.forEach(function (p, n) { p.tone = TONES[n % 5]; prodById[p.id] = p; });
    data.groups.forEach(function (g) { groupBy[g.key] = g; });

    // partners[ingredientId] -> list of interactions touching it; mine[ingredientId] -> products
    var partners = {}, mine = {};
    data.interactions.forEach(function (it) {
        (partners[it.a] = partners[it.a] || []).push(it);
        (partners[it.b] = partners[it.b] || []).push(it);
    });
    data.products.forEach(function (p) {
        p.ingredients.forEach(function (id) { (mine[id] = mine[id] || []).push(p); });
    });
    function toneOf(ing) { return (groupBy[ing.group] || {}).tone || 'lime'; }
    function sevLabel(s) { return s === 'high' ? 'High' : s === 'low' ? 'Low' : 'Moderate'; }
    var SEV_RANK = { high: 0, moderate: 1, medium: 1, low: 2 };
    var SEV_ICON = { high: '⚠️', moderate: '🌦️', medium: '🌦️', low: '🌤️' };

    /* ---------------- tabs ---------------- */
    var tabs = $$('.ih-tabs .pill');
    function showTab(name, push) {
        tabs.forEach(function (t) {
            var on = t.dataset.tab === name;
            t.classList.toggle('active', on); t.setAttribute('aria-selected', on ? 'true' : 'false'); t.tabIndex = on ? 0 : -1;
        });
        $('#panel-checker').hidden = name !== 'checker';
        $('#panel-guide').hidden = name !== 'guide';
        if (push !== false) { try { history.replaceState(null, '', location.pathname + location.search + (name === 'guide' ? '#guide' : '')); } catch (e) {} }
    }
    tabs.forEach(function (t) {
        t.addEventListener('click', function () { showTab(t.dataset.tab); });
        t.addEventListener('keydown', function (e) {
            if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
            var next = tabs[(tabs.indexOf(t) + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
            next.focus(); showTab(next.dataset.tab);
        });
    });

    /* ================= CHECKER ================= */
    var MAX = 8;
    var sel = [];                       // [{ t: 'p' | 'i', id }]
    var source = data.products.length ? 'products' : 'ingredients';

    function keyOf(it) { return it.t + it.id; }
    function find(t, id) { for (var i = 0; i < sel.length; i++) if (sel[i].t === t && sel[i].id === id) return i; return -1; }
    function nameOf(it) { return it.t === 'p' ? prodById[it.id].name : ingById[it.id].name; }
    function ingSet(it) { var o = {}; (it.t === 'p' ? prodById[it.id].ingredients : [it.id]).forEach(function (x) { o[x] = 1; }); return o; }

    function toggle(t, id, node) {
        var at = find(t, id);
        if (at !== -1) { sel.splice(at, 1); }
        else {
            if (sel.length >= MAX) { $('#pickCount').textContent = 'Max ' + MAX + ' at once'; setTimeout(paintCount, 1800); return; }
            sel.push({ t: t, id: id }); burstAt(node, 8);
        }
        refresh();
    }
    function paintCount() { $('#pickCount').textContent = sel.length + ' / ' + MAX; }

    /* ---- picker ---- */
    var grid = $('#pickGrid'), pickSearch = $('#pickSearch');

    function renderPicker() {
        var q = pickSearch.value.trim().toLowerCase(), shown = 0;
        grid.textContent = '';
        grid.className = 'pickgrid' + (source === 'ingredients' ? ' is-chips' : source === 'routines' ? ' is-rows' : '');

        if (source === 'products') {
            data.products.forEach(function (p) {
                if (q && (p.name + ' ' + p.brand + ' ' + p.category).toLowerCase().indexOf(q) === -1) return;
                shown++;
                var on = find('p', p.id) !== -1;
                var t = el('div', 'ptile tone-' + p.tone + (on ? ' is-on' : '')); t.setAttribute('role', 'button'); t.tabIndex = 0; t.setAttribute('aria-pressed', on ? 'true' : 'false');
                var im = el('span', 'ptile__img'); im.appendChild(art(p)); t.appendChild(im);
                t.appendChild(el('span', 'ptile__name', p.name)); t.appendChild(el('small', '', p.brand));
                t.appendChild(el('small', p.ingredients.length ? '' : 'warn', p.ingredients.length ? p.ingredients.length + ' ingredients' : 'No ingredients yet'));
                onActivate(t, function () { toggle('p', p.id, t); });
                grid.appendChild(t);
            });
            if (!shown) {
                var none = el('p', 'pickgrid__none');
                if (!data.products.length) {
                    none.appendChild(document.createTextNode('Your shelf is empty. '));
                    var a = el('a', '', 'Add a product'); a.href = root.dataset.addProduct; none.appendChild(a);
                    none.appendChild(document.createTextNode(' or pick from the ingredient list.'));
                } else none.textContent = 'No products match that search.';
                grid.appendChild(none);
            }
        } else if (source === 'ingredients') {
            data.ingredients.forEach(function (ing) {
                if (!ing.classified) return;
                if (q && (ing.name + ' ' + ing.function).toLowerCase().indexOf(q) === -1) return;
                shown++;
                var on = find('i', ing.id) !== -1;
                var c = el('span', 'ichip tone-' + toneOf(ing) + (on ? ' is-on' : ''), ing.name);
                c.setAttribute('role', 'button'); c.tabIndex = 0; c.setAttribute('aria-pressed', on ? 'true' : 'false'); c.title = ing.function;
                onActivate(c, function () { toggle('i', ing.id, c); });
                grid.appendChild(c);
            });
            if (!shown) grid.appendChild(el('p', 'pickgrid__none', 'No ingredients match that search.'));
        } else {
            data.routines.forEach(function (r) {
                if (q && r.name.toLowerCase().indexOf(q) === -1) return;
                shown++;
                var tone = r.type === 'evening' ? 'lav' : r.type === 'afternoon' ? 'sky' : 'sun';
                var emoji = r.type === 'evening' ? '🌙' : r.type === 'afternoon' ? '🌤️' : '☀️';
                var t = el('div', 'rtile tone-' + tone); t.setAttribute('role', 'button'); t.tabIndex = 0;
                t.appendChild(el('span', 'rtile__emoji', emoji));
                var body = el('div'); body.appendChild(el('strong', '', r.name)); body.appendChild(el('span', '', r.products.length + ' product' + (r.products.length === 1 ? '' : 's')));
                t.appendChild(body); t.appendChild(el('span', 'rtile__go', 'Check this'));
                onActivate(t, function () {
                    sel = r.products.slice(0, MAX).map(function (id) { return { t: 'p', id: id }; });
                    refresh(); burstAt(t, 12);
                });
                grid.appendChild(t);
            });
            if (!shown) {
                var n = el('p', 'pickgrid__none', data.routines.length ? 'No routines match that search.' : 'You have no routines with products yet. Build one in the Routines page and it will show up here.');
                grid.appendChild(n);
            }
        }
    }
    $$('.srcs .pill').forEach(function (b) {
        b.classList.toggle('active', b.dataset.src === source);
        b.addEventListener('click', function () {
            source = b.dataset.src; $$('.srcs .pill').forEach(function (x) { x.classList.toggle('active', x === b); });
            pickSearch.value = ''; renderPicker();
        });
    });
    pickSearch.addEventListener('input', renderPicker);
    pickSearch.addEventListener('keydown', function (e) { if (e.key === 'Enter') e.preventDefault(); });

    /* ---- stack ---- */
    function renderStack() {
        var list = $('#stackList'); list.textContent = '';
        sel.forEach(function (it) {
            var li = el('li', 'schip');
            if (it.t === 'p') {
                var p = prodById[it.id]; li.classList.add('tone-' + p.tone);
                var im = el('span', 'schip__img'); im.appendChild(art(p)); li.appendChild(im);
            } else {
                li.classList.add('tone-' + toneOf(ingById[it.id])); li.appendChild(el('span', 'schip__dot'));
            }
            li.appendChild(el('span', 'schip__name', nameOf(it)));
            var x = el('button', 'schip__x', '×'); x.type = 'button'; x.setAttribute('aria-label', 'Remove ' + nameOf(it));
            x.addEventListener('click', function () { toggle(it.t, it.id); });
            li.appendChild(x); list.appendChild(li);
        });
        $('#bowl').classList.toggle('has', sel.length > 0);
        $('#clearStack').hidden = !sel.length;
    }
    $('#clearStack').addEventListener('click', function () { sel = []; refresh(); });

    /* ---- analysis ---- */
    function analyse() {
        var sets = sel.map(ingSet), found = [], pairs = 0, bad = {};
        for (var i = 0; i < sel.length; i++) {
            for (var j = i + 1; j < sel.length; j++) {
                pairs++;
                data.interactions.forEach(function (it) {
                    if ((sets[i][it.a] && sets[j][it.b]) || (sets[i][it.b] && sets[j][it.a])) {
                        found.push({ x: sel[i], y: sel[j], it: it }); bad[i + '-' + j] = 1;
                    }
                });
            }
        }
        found.sort(function (p, q) { return (SEV_RANK[p.it.severity] != null ? SEV_RANK[p.it.severity] : 3) - (SEV_RANK[q.it.severity] != null ? SEV_RANK[q.it.severity] : 3); });
        return { found: found, pairs: pairs, badPairs: Object.keys(bad).length };
    }

    function badge(kind, icon, title, sevText) {
        var b = el('div', 'badge badge--' + kind); b.appendChild(el('span', 'badge__icon', icon));
        var body = el('div'); var s = el('strong', '', title);
        if (sevText) s.appendChild(el('span', 'sev', sevText));
        body.appendChild(s); b.appendChild(body); b._body = body; return b;
    }

    var lastLevel = null;
    function renderResults() {
        var n = sel.length, box = $('#findings'), v = $('#verdict');
        $('#resCount').textContent = n + ' item' + (n === 1 ? '' : 's');
        box.textContent = ''; $('#seen').textContent = '';

        var res = n >= 2 ? analyse() : null, level = 'empty';
        if (res) {
            var worst = res.found.reduce(function (m, f) { return Math.min(m, SEV_RANK[f.it.severity] != null ? SEV_RANK[f.it.severity] : 3); }, 9);
            level = !res.found.length ? 'clear' : worst === 0 ? 'high' : 'caution';
        }
        var copy = {
            empty: ['🌱', n === 1 ? 'Add one more' : 'Pick two or more', n === 1 ? 'Add another product or ingredient to see how they layer.' : "Add at least two products or ingredients and we'll compare them."],
            clear: ['🌿', 'Plays nicely', 'No flagged clashes between these. We only know about the combinations in our guide.'],
            caution: ['🌦️', 'Use with care', 'A few pairings can be irritating together. Space them out if your skin feels sensitive.'],
            high: ['⚠️', 'Better apart', 'Some of these are best used at different times. See the notes below.']
        }[level];
        v.dataset.state = level; $('#vFace').textContent = copy[0]; $('#vTitle').textContent = copy[1]; $('#vText').textContent = copy[2];
        if (level !== lastLevel && level !== 'empty') { v.classList.remove('pop'); void v.offsetWidth; v.classList.add('pop'); }
        lastLevel = level;

        var meter = $('#vMeter'); meter.hidden = !res;
        if (res) {
            var calm = res.pairs - res.badPairs;
            $('#vMeterLabel').textContent = calm + ' of ' + res.pairs + ' pair' + (res.pairs === 1 ? '' : 's') + ' get along';
            var fill = $('#vMeterFill'); fill.className = level === 'high' ? 'high' : level === 'caution' ? 'caution' : '';
            fill.style.width = Math.round(100 * calm / res.pairs) + '%';
        }

        if (res) res.found.forEach(function (f) {
            var a = ingById[f.it.a], b = ingById[f.it.b], sev = SEV_ICON[f.it.severity] ? f.it.severity : 'moderate';
            var bd = badge(sev, SEV_ICON[sev], a.name + ' + ' + b.name, sevLabel(sev));
            if (f.x.t === 'p' || f.y.t === 'p') bd._body.appendChild(el('p', 'who', nameOf(f.x) + '  ×  ' + nameOf(f.y)));
            bd._body.appendChild(el('p', '', f.it.message));
            if (f.it.tip) bd._body.appendChild(el('p', 'tip', '💡 ' + f.it.tip));
            var links = el('div', 'links');
            [a, b].forEach(function (ing) {
                var l = el('button', 'linkbtn', 'About ' + ing.name); l.type = 'button';
                l.addEventListener('click', function () { openGuide(ing.id); }); links.appendChild(l);
            });
            bd._body.appendChild(links); box.appendChild(bd);
        });
        if (res && !res.found.length) {
            box.appendChild((function () { var b = badge('ok', '✅', 'No known clashes'); b._body.appendChild(el('p', '', 'None of the pairs in this stack are flagged in our guide.')); return b; })());
        }

        // products with no ingredient list can't be compared
        sel.filter(function (it) { return it.t === 'p' && !prodById[it.id].ingredients.length; }).forEach(function (it) {
            var p = prodById[it.id], b = badge('info', '📝', p.name + ' was skipped');
            var para = el('p', '', 'It has no ingredients saved, so there was nothing to compare. ');
            var a = el('a', '', 'Add its ingredients'); a.href = p.url; para.appendChild(a); b._body.appendChild(para); box.appendChild(b);
        });

        if (res) {
            var all = {}; sel.forEach(function (it) { Object.keys(ingSet(it)).forEach(function (k) { all[k] = 1; }); });
            $('#seen').textContent = 'Compared ' + Object.keys(all).length + ' ingredient' + (Object.keys(all).length === 1 ? '' : 's') + ' across ' + n + ' items.';
        }
    }

    function refresh() { paintCount(); renderStack(); renderPicker(); renderResults(); }

    /* ================= GUIDE ================= */
    var gSearch = $('#guideSearch'), gGrid = $('#guideGrid'), gPills = $('#groupPills');
    var gState = { group: 'all', q: '', clashOnly: false };

    var counts = { all: 0, clash: 0 };
    data.ingredients.forEach(function (i) {
        if (i.classified) counts.all++;
        counts[i.group] = (counts[i.group] || 0) + 1;
        if (i.classified && (partners[i.id] || []).length) counts.clash++;
    });

    function pill(label, key, count, extra) {
        var b = el('button', 'pill', label + ' '); b.type = 'button'; b.dataset.group = key;
        b.appendChild(el('b', '', String(count)));
        if (extra) b.dataset.extra = extra;
        return b;
    }
    function renderPills() {
        gPills.textContent = '';
        gPills.appendChild(pill('All', 'all', counts.all));
        data.groups.forEach(function (g) { if (counts[g.key]) gPills.appendChild(pill(g.key === 'other' ? 'Needs info' : g.label, g.key, counts[g.key])); });
        var c = pill('⚠ Has clash notes', 'clash', counts.clash); gPills.appendChild(c);
        paintPills();
    }
    function paintPills() {
        $$('.pill', gPills).forEach(function (b) {
            var on = b.dataset.group === 'clash' ? gState.clashOnly : (b.dataset.group === gState.group);
            b.classList.toggle('active', on); b.setAttribute('aria-pressed', on ? 'true' : 'false');
        });
    }
    gPills.addEventListener('click', function (e) {
        var b = e.target.closest('.pill'); if (!b) return;
        if (b.dataset.group === 'clash') gState.clashOnly = !gState.clashOnly; else gState.group = b.dataset.group;
        paintPills(); renderGuide();
    });
    gSearch.addEventListener('input', function () { gState.q = gSearch.value.trim().toLowerCase(); renderGuide(); });
    gSearch.addEventListener('keydown', function (e) { if (e.key === 'Enter') e.preventDefault(); });
    function resetGuide() { gState = { group: 'all', q: '', clashOnly: false }; gSearch.value = ''; paintPills(); renderGuide(); }
    $('#guideReset').addEventListener('click', resetGuide);

    function renderGuide() {
        gGrid.textContent = '';
        var shown = 0;
        data.ingredients.forEach(function (ing) {
            var inAll = gState.group === 'all' && (ing.classified || gState.q);
            if (!(inAll || ing.group === gState.group)) return;
            if (gState.clashOnly && !(partners[ing.id] || []).length) return;
            if (gState.q && (ing.name + ' ' + ing.function + ' ' + ing.description).toLowerCase().indexOf(gState.q) === -1) return;
            shown++;
            var g = groupBy[ing.group] || {}, np = (partners[ing.id] || []).length, nm = (mine[ing.id] || []).length;
            var c = el('article', 'icard tone-' + toneOf(ing)); c.setAttribute('role', 'button'); c.tabIndex = 0; c.dataset.id = ing.id;
            c.style.animationDelay = Math.min(shown, 12) * 25 + 'ms';
            c.appendChild(el('span', 'icard__grp', g.label || ''));
            c.appendChild(el('h3', '', ing.name));
            c.appendChild(el('p', 'icard__fn', ing.classified ? ing.function : 'Not classified yet'));
            c.appendChild(el('p', 'icard__desc', ing.description));
            var foot = el('div', 'icard__foot');
            if (np) foot.appendChild(el('span', 'mini mini--warn', '⚠ ' + np + ' pairing note' + (np === 1 ? '' : 's')));
            if (nm) foot.appendChild(el('span', 'mini mini--mine', '🌿 In ' + nm + ' of your products'));
            c.appendChild(foot);
            onActivate(c, function () { openDetail(ing.id); });
            gGrid.appendChild(c);
        });
        $('#guideEmpty').hidden = shown > 0; gGrid.hidden = shown === 0;
        var label = gState.group === 'all' ? 'ingredients' : ((groupBy[gState.group] || {}).label || 'ingredients').toLowerCase();
        $('#guideMeta').textContent = shown ? 'Showing ' + shown + ' ' + (shown === 1 && label === 'ingredients' ? 'ingredient' : label) + (gState.q ? ' for “' + gSearch.value.trim() + '”' : '') : '';
    }

    /* ---- detail dialog ---- */
    var dlg = $('#ingDialog'), openId = null;
    $$('[data-close]', dlg).forEach(function (b) { b.addEventListener('click', function () { dlg.close(); }); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });

    function openDetail(id) {
        var ing = ingById[id]; if (!ing) return; openId = id;
        var g = groupBy[ing.group] || {};
        var chip = $('#dGroup'); chip.textContent = g.label || ''; chip.className = 'chip chip--' + ({ lime: '', sky: 'sky', pink: 'pink', sun: 'sun', lav: 'lav' }[g.tone] || '');
        $('#dName').textContent = ing.name;
        $('#dFn').textContent = ing.classified ? ing.function : 'Not classified yet';
        $('#dDesc').textContent = ing.description;
        var c = $('#dCaution'); c.hidden = !ing.caution; c.textContent = ing.caution ? '🌦️ ' + ing.caution : '';

        var ps = (partners[id] || []).slice().sort(function (a, b) { return (SEV_RANK[a.severity] != null ? SEV_RANK[a.severity] : 3) - (SEV_RANK[b.severity] != null ? SEV_RANK[b.severity] : 3); });
        var pl = $('#dPartners'); pl.textContent = ''; $('#dPartnersSec').hidden = !ps.length;
        ps.forEach(function (it) {
            var other = ingById[it.a === id ? it.b : it.a], li = el('li'), b = el('b', '', other.name);
            li.appendChild(b); li.appendChild(el('span', 'sev ' + it.severity, sevLabel(it.severity)));
            li.appendChild(document.createElement('br')); li.appendChild(document.createTextNode(it.message));
            if (it.tip) li.appendChild(el('em', '', '💡 ' + it.tip));
            pl.appendChild(li);
        });

        var mp = mine[id] || [], ml = $('#dProducts'); ml.textContent = ''; $('#dProductsSec').hidden = !mp.length;
        mp.forEach(function (p) { var li = el('li'), a = el('a', '', p.name); a.href = p.url; a.title = p.brand + ' · ' + p.name; li.appendChild(a); ml.appendChild(li); });

        var all = $('#dFindAll'); all.hidden = !mp.length;
        all.href = (root.dataset.libraryUrl || '/products/') + '?ingredient=' + encodeURIComponent(ing.name);

        $('#dCheck').textContent = find('i', id) !== -1 ? 'Already in my stack' : 'Check with my stack';
        if (dlg.showModal) dlg.showModal();
    }
    $('#dCheck').addEventListener('click', function () {
        if (openId == null) return;
        if (find('i', openId) === -1 && sel.length < MAX) sel.push({ t: 'i', id: openId });
        source = source === 'routines' ? 'products' : source;
        dlg.close(); showTab('checker'); refresh();
        var st = $('#bowl'); if (st) { st.scrollIntoView({ behavior: 'smooth', block: 'center' }); burstAt(st, 10); }
    });

    function openGuide(id) { showTab('guide'); var ing = ingById[id]; if (ing) { gSearch.value = ing.name; gState.q = ing.name.toLowerCase(); gState.group = 'all'; paintPills(); renderGuide(); openDetail(id); } }

    /* ================= go ================= */
    renderPills(); renderGuide(); refresh();

    var params = new URLSearchParams(location.search), q0 = (params.get('q') || '').trim();
    if (q0) { gSearch.value = q0; gState.q = q0.toLowerCase(); renderGuide(); showTab('guide', false); }
    else if (location.hash === '#guide' || params.get('tab') === 'guide') showTab('guide', false);
});
