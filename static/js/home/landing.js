document.addEventListener('DOMContentLoaded', function () {
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ---------- Hero product stage ---------- */
    var items = [
        { script: 'Gentle', name: 'Soft Cleanser', type: 'Cleanser · Water, Glycerin, Ceramides', art: 'a-pump', tone: 'lime' },
        { script: 'Glow',   name: 'Vitamin C Serum', type: 'Serum · Vitamin C, Hyaluronic Acid', art: 'a-dropper', tone: 'sky' },
        { script: 'Cozy',   name: 'Barrier Cream', type: 'Moisturizer · Ceramides, Squalane', art: 'a-jar', tone: 'pink' },
        { script: 'Daily',  name: 'Light SPF 50', type: 'Sunscreen · Zinc Oxide, Glycerin', art: 'a-tube', tone: 'sun' }
    ];
    var panel = document.getElementById('stagePanel');
    var art = document.getElementById('stageArt');
    var thumbs = document.querySelectorAll('#stageThumbs .thumb');
    var idx = 0, timer = null, hover = false;

    function show(i) {
        idx = (i + items.length) % items.length;
        var it = items[idx];
        panel.className = 'stage__panel tone-' + it.tone;
        art.classList.remove('swap'); void art.getBoundingClientRect(); art.classList.add('swap');
        art.firstElementChild.setAttribute('href', '#' + it.art);
        document.getElementById('stageScript').textContent = it.script;
        document.getElementById('stageName').textContent = it.name;
        document.getElementById('stageType').textContent = it.type;
        thumbs.forEach(function (t, n) { t.classList.toggle('active', n === idx); t.setAttribute('aria-selected', n === idx); });
    }
    function start() { if (reduce) return; stop(); timer = setInterval(function () { if (!hover) show(idx + 1); }, 4200); }
    function stop() { clearInterval(timer); }

    thumbs.forEach(function (t, n) { t.addEventListener('click', function () { show(n); start(); }); });
    document.getElementById('stagePrev').addEventListener('click', function () { show(idx - 1); start(); });
    document.getElementById('stageNext').addEventListener('click', function () { show(idx + 1); start(); });
    var stage = document.getElementById('stage');
    stage.addEventListener('mouseenter', function () { hover = true; });
    stage.addEventListener('mouseleave', function () { hover = false; });
    show(0); start();

    // parallax on the floating cards
    if (!reduce) stage.addEventListener('pointermove', function (e) {
        var r = stage.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
        stage.style.setProperty('--mx', (x * 14).toFixed(1) + 'px');
        stage.style.setProperty('--my', (y * 14).toFixed(1) + 'px');
    });

    /* ---------- Mini routine card ---------- */
    var mini = document.getElementById('miniRoutine'), count = document.getElementById('miniCount');
    function recount() {
        var steps = mini.querySelectorAll('.mstep'), done = mini.querySelectorAll('.mstep.done').length;
        count.textContent = done + '/' + steps.length;
        mini.classList.toggle('all-done', done === steps.length);
    }
    mini.querySelectorAll('.mstep').forEach(function (b) {
        b.addEventListener('click', function (e) {
            b.classList.toggle('done'); recount();
            if (b.classList.contains('done') && mini.classList.contains('all-done') && window.FV && FV.burst) {
                var r = mini.getBoundingClientRect(); FV.burst(r.left + r.width / 2, r.top + 30, 14);
            }
        });
    });
    recount();

    /* ---------- Clash demo ---------- */
    var rules = [
        ['retinol', 'glycolic acid', 'high', 'Both are exfoliating. Layering them may cause redness, peeling or stinging.', 'Try them on alternate nights.'],
        ['retinol', 'salicylic acid', 'high', 'Retinol plus a BHA can be very drying for some skin.', 'Use on separate nights, or BHA in the morning and retinol at night.'],
        ['retinol', 'benzoyl peroxide', 'high', 'Benzoyl peroxide can make retinol less stable and more irritating together.', 'Apply them at different times of day.'],
        ['retinol', 'vitamin c', 'moderate', 'Both are active ingredients and can irritate when layered.', 'Vitamin C in the morning, retinol at night.'],
        ['glycolic acid', 'vitamin c', 'moderate', 'Acids plus vitamin C may sting on sensitive skin.', 'Space them apart or alternate days.'],
        ['glycolic acid', 'salicylic acid', 'moderate', 'Two exfoliating acids at once can over-exfoliate.', 'Pick one per routine.']
    ];
    var chips = document.querySelectorAll('#demoChips .ichip'), picked = [];
    var slotA = document.getElementById('slotA'), slotB = document.getElementById('slotB'), out = document.getElementById('demoOut');
    function label(k) { var c = document.querySelector('#demoChips [data-i="' + k + '"]'); return c ? c.textContent : k; }
    function render() {
        chips.forEach(function (c) { c.classList.toggle('on', picked.indexOf(c.dataset.i) !== -1); c.setAttribute('aria-pressed', picked.indexOf(c.dataset.i) !== -1); });
        slotA.textContent = picked[0] ? label(picked[0]) : 'Pick one…';
        slotB.textContent = picked[1] ? label(picked[1]) : 'Pick another…';
        slotA.classList.toggle('filled', !!picked[0]); slotB.classList.toggle('filled', !!picked[1]);
        out.textContent = '';
        var box = document.createElement('div');
        if (picked.length < 2) { box.className = 'res res--idle'; box.innerHTML = '<p>Choose two ingredients above.</p>'; }
        else {
            var hit = rules.filter(function (r) { return (r[0] === picked[0] && r[1] === picked[1]) || (r[0] === picked[1] && r[1] === picked[0]); })[0];
            if (hit) {
                box.className = 'res res--' + hit[2];
                var h = document.createElement('strong'); h.textContent = (hit[2] === 'high' ? '⚠️ Take care: ' : '🌦️ Heads up: ') + label(picked[0]) + ' + ' + label(picked[1]);
                var p = document.createElement('p'); p.textContent = hit[3];
                var t = document.createElement('p'); t.className = 'tip'; t.textContent = '💡 ' + hit[4];
                box.append(h, p, t);
            } else {
                box.className = 'res res--ok';
                var h2 = document.createElement('strong'); h2.textContent = '✅ No known clash';
                var p2 = document.createElement('p'); p2.textContent = 'We don\'t have a flagged interaction for this pair, which only covers combinations we know about.';
                box.append(h2, p2);
            }
        }
        out.appendChild(box);
    }
    chips.forEach(function (c) {
        c.addEventListener('click', function () {
            var k = c.dataset.i, at = picked.indexOf(k);
            if (at !== -1) picked.splice(at, 1);
            else { if (picked.length === 2) picked.shift(); picked.push(k); }
            render();
        });
    });
    render();
});
