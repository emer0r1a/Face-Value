document.addEventListener('DOMContentLoaded', function () {
    var rb = document.getElementById('rb');
    if (!rb) return;

    function $(s, r) { return (r || document).querySelector(s); }
    function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
    function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text) n.textContent = text; return n; }
    function csrf() { var m = document.cookie.match(/csrftoken=([^;]+)/); return m ? decodeURIComponent(m[1]) : ''; }

    var routines = [];
    try { routines = JSON.parse($('#rb-routines').textContent); } catch (e) {}
    function byId(id) { return routines.filter(function (r) { return r.id === id; })[0]; }

    var scheduleUrl = rb.dataset.scheduleUrl, newUrl = rb.dataset.newUrl;

    /* ---------- dialogs ---------- */
    $$('dialog [data-close]').forEach(function (b) { b.addEventListener('click', function () { b.closest('dialog').close(); }); });
    $$('dialog').forEach(function (d) { d.addEventListener('click', function (e) { if (e.target === d) d.close(); }); });

    /* ---------- delete ---------- */
    var delDlg = $('#deleteDialog'), delForm = $('#deleteForm'), delTpl = $('#deleteUrlTpl');
    $$('[data-delete]').forEach(function (b) {
        b.addEventListener('click', function () {
            delForm.action = delTpl.innerHTML.trim().replace('/0/', '/' + b.dataset.delete + '/');
            $('#deleteTitle').textContent = 'Remove “' + b.dataset.name + '”?';
            if (delDlg.showModal) delDlg.showModal();
        });
    });

    /* ---------- planner ---------- */
    var cellDlg = $('#cellDialog'), cellList = $('#cellList'), cellStatus = $('#cellStatus');
    var current = null;   // { slot, day, label }

    function cellFor(slot, day) { return $('.pcell[data-slot="' + slot + '"][data-day="' + day + '"]'); }

    function paintCell(slot, day) {
        var cell = cellFor(slot, day); if (!cell) return;
        var list = $('.pcell__list', cell); list.textContent = '';
        routines.forEach(function (r) {
            if (r.type !== slot || r.days.indexOf(day) === -1) return;
            var chip = el('span', 'pchip' + (r.paused ? ' is-paused' : ''), r.name);
            chip.dataset.id = r.id; list.appendChild(chip);
        });
    }

    function paintCard(r) {
        $$('.rcard[data-routine="' + r.id + '"] .rdays__d').forEach(function (d) {
            d.classList.toggle('on', r.days.indexOf(d.dataset.day) !== -1);
        });
    }

    function paintStats() {
        var n = 0;
        routines.forEach(function (r) { if (!r.paused) n += r.days.length; });
        var s = $('#statWeek'); if (s) s.textContent = n;
    }

    function say(msg, bad) { cellStatus.textContent = msg || ''; cellStatus.classList.toggle('err', !!bad); }

    function openCell(cell) {
        current = { slot: cell.dataset.slot, day: cell.dataset.day, label: cell.dataset.label };
        $('#cellTitle').textContent = current.label.replace(' · ', ' · ');
        cellList.textContent = ''; say('');
        var mine = routines.filter(function (r) { return r.type === current.slot; });
        if (!mine.length) {
            var li = el('li'); li.appendChild(el('p', 'muted-line', 'No ' + current.slot + ' routines yet. Make one and it will appear here.'));
            cellList.appendChild(li);
        }
        mine.forEach(function (r) {
            var li = el('li'), lab = el('label', 'sw' + (r.paused ? ' is-paused' : ''));
            var cb = el('input'); cb.type = 'checkbox'; cb.checked = r.days.indexOf(current.day) !== -1;
            lab.appendChild(cb);
            lab.appendChild(el('span', '', r.name + (r.paused ? ' (paused)' : '')));
            lab.appendChild(el('span', 'sw__track'));
            cb.addEventListener('change', function () { toggle(r, cb); });
            li.appendChild(lab); cellList.appendChild(li);
        });
        $('#cellNew').href = newUrl + '?type=' + encodeURIComponent(current.slot) + '&day=' + encodeURIComponent(current.day);
        if (cellDlg.showModal) cellDlg.showModal();
    }

    function toggle(r, cb) {
        var want = cb.checked, slot = current.slot, day = current.day;
        cb.disabled = true; say('Saving…');
        fetch(scheduleUrl.replace('/0/', '/' + r.id + '/'), {
            method: 'POST', credentials: 'same-origin',
            headers: { 'X-CSRFToken': csrf(), 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ day: day, on: want ? '1' : '0' })
        }).then(function (res) { if (!res.ok) throw new Error(); return res.json(); })
          .then(function (d) {
              r.days = d.days; paintCell(slot, day); paintCard(r); paintStats();
              say(want ? 'Added to ' + r.name + '.' : 'Removed from this day.');
              if (want && window.FV && FV.burst) { var b = cb.getBoundingClientRect(); FV.burst(b.left + b.width / 2, b.top + b.height / 2, 10); }
          })
          .catch(function () { cb.checked = !want; say("Couldn't save that. Please try again.", true); })
          .then(function () { cb.disabled = false; });
    }

    $$('.pcell').forEach(function (c) { c.addEventListener('click', function () { openCell(c); }); });
});
