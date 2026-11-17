document.addEventListener('DOMContentLoaded', function () {
    var dash = document.querySelector('.dash');
    if (!dash) return;
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function $(s, r) { return (r || document).querySelector(s); }
    function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
    function csrf() { var m = document.cookie.match(/csrftoken=([^;]+)/); return m ? decodeURIComponent(m[1]) : ''; }
    function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text) n.textContent = text; return n; }
    function pad(n) { return (n < 10 ? '0' : '') + n; }
    function burstAt(node) {
        if (!(window.FV && FV.burst)) return;
        var r = node.getBoundingClientRect(); FV.burst(r.left + r.width / 2, r.top + r.height / 2, 14);
    }

    /* ============ Shelf carousel ============ */
    (function () {
        var shelf = $('#shelf'); if (!shelf) return;
        var slides = $$('.slide', shelf), thumbs = $$('.sthumb', shelf), count = $('#shelfCount');
        var idx = 0, timer = null, paused = false;

        function show(i, dir) {
            if (!slides.length) return;
            var old = slides[idx];
            idx = (i + slides.length) % slides.length;
            slides.forEach(function (s, n) {
                s.classList.toggle('active', n === idx);
                s.classList.toggle('leaving', n !== idx && n === slides.indexOf(old) && dir !== -1);
                s.setAttribute('aria-hidden', n === idx ? 'false' : 'true');
            });
            shelf.className = shelf.className.replace(/\btone-\w+/g, '').trim() + ' tone-' + slides[idx].dataset.tone;
            thumbs.forEach(function (t, n) { t.classList.toggle('active', n === idx); t.setAttribute('aria-selected', n === idx); });
            if (count) count.textContent = pad(idx + 1) + ' / ' + pad(slides.length);
            var a = thumbs[idx]; if (a && a.scrollIntoView) a.scrollIntoView({ block: 'nearest', inline: 'nearest' });
        }
        function start() { stop(); if (reduce || slides.length < 2) return; timer = setInterval(function () { if (!paused) show(idx + 1); }, 5500); }
        function stop() { clearInterval(timer); }
        function go(n, d) { show(n, d); start(); }

        thumbs.forEach(function (t, n) { t.addEventListener('click', function () { go(n); }); });
        var p = $('#shelfPrev'), n = $('#shelfNext');
        if (p) p.addEventListener('click', function () { go(idx - 1, -1); });
        if (n) n.addEventListener('click', function () { go(idx + 1); });
        shelf.addEventListener('mouseenter', function () { paused = true; });
        shelf.addEventListener('mouseleave', function () { paused = false; });
        shelf.addEventListener('focusin', function () { paused = true; });
        shelf.addEventListener('focusout', function () { paused = false; });
        shelf.addEventListener('keydown', function (e) {
            if (e.key === 'ArrowRight') { go(idx + 1); e.preventDefault(); }
            if (e.key === 'ArrowLeft') { go(idx - 1, -1); e.preventDefault(); }
        });
        var x0 = null;
        shelf.addEventListener('pointerdown', function (e) { x0 = e.clientX; });
        shelf.addEventListener('pointerup', function (e) {
            if (x0 === null) return; var dx = e.clientX - x0; x0 = null;
            if (Math.abs(dx) > 50) go(dx < 0 ? idx + 1 : idx - 1, dx < 0 ? 1 : -1);
        });
        show(0); start();
    })();

    /* ============ Count-up + rings ============ */
    function countUp(node) {
        var end = +node.dataset.count || 0;
        if (reduce || end === 0) { node.textContent = end; return; }
        var t0 = null, dur = 900;
        node.textContent = '0';
        function step(t) { if (!t0) t0 = t; var k = Math.min((t - t0) / dur, 1); node.textContent = Math.round(end * (1 - Math.pow(1 - k, 3))); if (k < 1) requestAnimationFrame(step); }
        requestAnimationFrame(step);
    }
    if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { countUp(e.target); io.unobserve(e.target); } }); }, { threshold: .4 });
        $$('[data-count]').forEach(function (n) { io.observe(n); });
    } else { $$('[data-count]').forEach(countUp); }

    function setRing(circle, pct) { circle.style.strokeDashoffset = 97.4 * (1 - Math.max(0, Math.min(100, pct)) / 100); }
    $$('.ring--stat .ring__fg').forEach(function (c) { setTimeout(function () { setRing(c, +c.dataset.pct || 0); }, 250); });
    $$('.vibe__item').forEach(function (item) { setTimeout(function () { setRing($('.ring__fg', item), +item.dataset.value || 0); }, 300); });

    /* ============ Routine tabs ============ */
    var tabs = $('#routineTabs');
    if (tabs) tabs.addEventListener('click', function (e) {
        var b = e.target.closest('.tab'); if (!b) return;
        $$('.tab', tabs).forEach(function (t) { t.classList.toggle('active', t === b); t.setAttribute('aria-selected', t === b); });
        $$('.routine').forEach(function (r) { r.hidden = !(b.dataset.filter === 'all' || r.dataset.type === b.dataset.filter); });
    });

    /* ============ Routine tracker ============ */
    var toggleBase = dash.dataset.toggleUrl;
    var streakNum = $('#streakNum'), streakBadge = $('#streakBadge'), doneChip = $('#doneChip');
    var tileDone = $('.stat.tone-sky'), tileStreak = $('.stat.tone-lime');

    function refreshDone() {
        var all = $$('.routine').length, done = $$('.routine.is-done').length;
        var pct = all ? Math.round(100 * done / all) : 0;
        if (doneChip) doneChip.textContent = done + '/' + all;
        if (tileDone) {
            setRing($('.ring__fg', tileDone), pct);
            $('[data-count]', tileDone).textContent = pct;
            $('em', tileDone).textContent = done + ' of ' + all + ' routines';
        }
    }
    function paint(routine) {
        var boxes = $$('input[type=checkbox]', routine), n = boxes.length, c = boxes.filter(function (b) { return b.checked; }).length;
        var pct = n ? Math.round(100 * c / n) : 0;
        $('.leafbar i', routine).style.width = pct + '%';
        $('.leafbar .leaf', routine).style.left = pct + '%';
        $('.routine__pct', routine).textContent = pct + '%';
        return { all: n > 0 && c === n };
    }
    function save(routine, done) {
        var url = toggleBase.replace('/0/', '/' + routine.dataset.routine + '/');
        return fetch(url, { method: 'POST', credentials: 'same-origin', headers: { 'X-CSRFToken': csrf(), 'Content-Type': 'application/x-www-form-urlencoded' }, body: new URLSearchParams({ done: done ? '1' : '0' }) })
            .then(function (r) { if (!r.ok) throw new Error(); return r.json(); });
    }
    $$('.routine').forEach(function (routine) {
        paint(routine);
        routine.addEventListener('change', function (e) {
            var state = paint(routine), was = routine.classList.contains('is-done');
            if (state.all === was) return;
            routine.classList.toggle('is-done', state.all); refreshDone();
            if (state.all) burstAt(e.target.nextElementSibling || e.target);
            save(routine, state.all).then(function (d) {
                streakNum.textContent = d.streak;
                if (tileStreak) { $('[data-count]', tileStreak).textContent = d.streak; $('em', tileStreak).textContent = 'Best: ' + d.best; }
                var today = $('.week__day[data-today="1"]');
                if (state.all) { streakBadge.classList.remove('pop'); void streakBadge.offsetWidth; streakBadge.classList.add('pop'); if (today && d.streak > 0) today.classList.add('done'); }
                else if (today && !$('.routine.is-done')) today.classList.remove('done');
            }).catch(function () {
                routine.classList.toggle('is-done', was);
                $$('input[type=checkbox]', routine).forEach(function (b) { b.checked = was; });
                paint(routine); refreshDone();
                alert("Couldn't save that just now. Please try again.");
            });
        });
    });

    /* ============ Daily check-in (mood + water, stored on this device) ============ */
    (function () {
        var moods = $('#moods'); if (!moods) return;
        var msgs = {
            dry: 'A little dry? Layer a hydrating serum under your moisturizer, and go easy on exfoliating today.',
            calm: 'Steady and calm. Stick to your usual routine and keep going.',
            good: 'Nice! Consistency is doing its job.',
            glow: 'Glow mode! Keep it going with SPF in the morning.',
            irritated: 'Keep it simple today: gentle cleanser, moisturizer and SPF. If it lingers, a dermatologist can help.'
        };
        var d = new Date(), key = 'fv-checkin-' + d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
        var state = { mood: '', water: 0 };
        try { var s = JSON.parse(localStorage.getItem(key) || 'null'); if (s) state = s; } catch (e) {}
        function persist() { try { localStorage.setItem(key, JSON.stringify(state)); } catch (e) {} }
        var msg = $('#moodMsg'), drops = $$('#drops .drop'), wc = $('#waterCount');

        function render() {
            $$('.mood', moods).forEach(function (m) { m.setAttribute('aria-checked', m.dataset.mood === state.mood ? 'true' : 'false'); });
            msg.textContent = state.mood ? msgs[state.mood] : 'Tap one to get a gentle tip for today.';
            drops.forEach(function (b, i) { b.classList.toggle('on', i < state.water); });
            wc.textContent = state.water + '/8';
        }
        moods.addEventListener('click', function (e) { var m = e.target.closest('.mood'); if (!m) return; state.mood = state.mood === m.dataset.mood ? '' : m.dataset.mood; persist(); render(); });
        drops.forEach(function (b, i) {
            b.addEventListener('click', function () {
                state.water = (state.water === i + 1) ? i : i + 1; persist(); render();
                if (state.water === 8) burstAt(b);
            });
        });
        render();
    })();

    /* ============ Tips carousel ============ */
    (function () {
        var track = $('#tipTrack'); if (!track) return;
        var bar = $('#tipBar');
        function by(dir) { var card = $('.tipcard', track); track.scrollBy({ left: dir * (card.offsetWidth + 20), behavior: reduce ? 'auto' : 'smooth' }); }
        $('#tipPrev').addEventListener('click', function () { by(-1); });
        $('#tipNext').addEventListener('click', function () { by(1); });
        function upd() {
            var max = track.scrollWidth - track.clientWidth;
            var w = Math.max(12, 100 * track.clientWidth / track.scrollWidth);
            bar.style.width = w + '%';
            bar.style.marginLeft = (max > 0 ? (100 - w) * track.scrollLeft / max : 0) + '%';
        }
        track.addEventListener('scroll', upd, { passive: true }); window.addEventListener('resize', upd); upd();
    })();

    /* ============ Clash checker (tap two products) ============ */
    (function () {
        var picks = $('#picks'), out = $('#clashOut'); if (!picks || !out) return;
        var slotA = $('#slotA'), slotB = $('#slotB'), chosen = [];
        var icons = { high: '⚠️', moderate: '🌦️', medium: '🌦️', low: '🌤️' };
        function badge(kind, icon, title, text, tip) {
            var box = el('div', 'badge badge--' + kind); box.appendChild(el('span', 'badge__icon', icon));
            var body = el('div'); body.appendChild(el('strong', '', title)); body.appendChild(el('p', '', text));
            if (tip) body.appendChild(el('p', 'tip', '💡 ' + tip)); box.appendChild(body); return box;
        }
        function nameOf(id) { var b = $('[data-id="' + id + '"] .pick__name', picks); return b ? b.textContent : ''; }
        function render() {
            $$('.pick', picks).forEach(function (b) { b.setAttribute('aria-pressed', chosen.indexOf(b.dataset.id) !== -1 ? 'true' : 'false'); });
            slotA.textContent = chosen[0] ? nameOf(chosen[0]) : 'Pick one…'; slotA.classList.toggle('filled', !!chosen[0]);
            slotB.textContent = chosen[1] ? nameOf(chosen[1]) : 'Pick another…'; slotB.classList.toggle('filled', !!chosen[1]);
            out.textContent = '';
            if (chosen.length < 2) return;
            fetch(dash.dataset.clashUrl + '?a=' + chosen[0] + '&b=' + chosen[1], { credentials: 'same-origin' })
                .then(function (r) { return r.json(); })
                .then(function (d) {
                    out.textContent = '';
                    if (d.error) { out.appendChild(badge('info', 'ℹ️', 'Hmm', d.error)); return; }
                    if (!d.has_ingredients) { out.appendChild(badge('info', '📝', 'Missing ingredients', 'One of these products has no ingredients saved yet, so there is nothing to compare.')); return; }
                    if (!d.clashes.length) { out.appendChild(badge('ok', '✅', 'No known clashes', "We didn't find a flagged interaction between these two. That only covers the combinations we know about.")); return; }
                    d.clashes.forEach(function (c) { var sev = icons[c.severity] ? c.severity : 'moderate'; out.appendChild(badge(sev, icons[sev], c.pair, c.message, c.tip)); });
                })
                .catch(function () { out.appendChild(badge('info', '☁️', "Couldn't check right now", 'Please try again in a moment.')); });
        }
        picks.addEventListener('click', function (e) {
            var b = e.target.closest('.pick'); if (!b) return;
            var id = b.dataset.id, at = chosen.indexOf(id);
            if (at !== -1) chosen.splice(at, 1); else { if (chosen.length === 2) chosen.shift(); chosen.push(id); }
            render();
        });
        render();
    })();
});
