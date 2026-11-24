(() => {
    "use strict";
    const $ = (id) => document.getElementById(id);
    const dataEl = $("tracker-data");
    if (!dataEl) return;
    const D = JSON.parse(dataEl.textContent);
    const KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
    const DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

    // ---------- dates ----------
    const pad = (n) => String(n).padStart(2, "0");
    const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
    const parse = (s) => { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); };
    const addDays = (d, n) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
    const wk = (d) => (d.getDay() + 6) % 7; // Mon = 0
    const today = parse(D.today);
    const todayIso = D.today;
    const WINDOW = D.window || 7;

    const state = {
        logs: {},
        summary: D.summary,
        sel: todayIso,
        calY: today.getFullYear(),
        calM: today.getMonth(),
        open: new Set(),
        busy: new Set(),
    };
    Object.entries(D.logs || {}).forEach(([k, ids]) => { state.logs[k] = new Set(ids); });
    const routines = D.routines.map((r) => ({ ...r, dayset: new Set(r.days || []), createdD: parse(r.created) }));

    const dueOn = (r, d) => {
        if (d < r.createdD) return false;
        return r.dayset.size === 0 || r.dayset.has(KEYS[wk(d)]);
    };
    const dueList = (d) => routines.filter((r) => dueOn(r, d));
    const doneSet = (d) => state.logs[iso(d)] || new Set();
    const stats = (d) => {
        const due = dueList(d), ok = doneSet(d);
        return { due: due.length, done: due.filter((r) => ok.has(r.id)).length };
    };
    const inWindow = (d) => d <= today && d > addDays(today, -WINDOW);

    // ---------- tiny DOM helpers ----------
    const el = (tag, cls, text) => {
        const n = document.createElement(tag);
        if (cls) n.className = cls;
        if (text != null) n.textContent = text;
        return n;
    };
    const svgUse = (id, cls) => {
        const ns = "http://www.w3.org/2000/svg";
        const s = document.createElementNS(ns, "svg");
        s.setAttribute("viewBox", "0 0 24 24");
        s.setAttribute("aria-hidden", "true");
        if (cls) s.setAttribute("class", cls);
        const u = document.createElementNS(ns, "use");
        u.setAttribute("href", "#" + id);
        s.appendChild(u);
        return s;
    };
    const clear = (n) => { while (n.firstChild) n.removeChild(n.firstChild); };
    const burst = (node, n) => {
        if (reduce || !window.FV || !FV.burst || !node) return;
        const r = node.getBoundingClientRect();
        FV.burst(r.left + r.width / 2, r.top + r.height / 2, n || 14);
    };
    const cookie = (name) => (document.cookie.split("; ").find((c) => c.startsWith(name + "=")) || "").split("=")[1] || "";
    let toastTimer;
    const toast = (msg) => {
        const t = $("trToast");
        t.textContent = msg;
        t.hidden = false;
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => { t.hidden = true; }, 3200);
    };
    const countTo = (node, to) => {
        const from = Number(node.textContent) || 0;
        if (reduce || from === to) { node.textContent = to; return; }
        const t0 = performance.now(), dur = 600;
        const tick = (t) => {
            const p = Math.min(1, (t - t0) / dur);
            node.textContent = Math.round(from + (to - from) * (1 - Math.pow(1 - p, 3)));
            if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
    };

    // ---------- step progress (device only) ----------
    const stepKey = (day, id) => `fv-trk-${day}-${id}`;
    const getSteps = (day, id) => { try { return new Set(JSON.parse(localStorage.getItem(stepKey(day, id)) || "[]")); } catch (e) { return new Set(); } };
    const setSteps = (day, id, set) => { try { localStorage.setItem(stepKey(day, id), JSON.stringify([...set])); } catch (e) { /* storage unavailable */ } };

    // ---------- hero ----------
    const MILESTONES = [3, 7, 14, 30, 60, 100, 200, 365];
    let medalPrev = null;
    const renderHero = () => {
        const s = state.summary;
        countTo($("streakNum"), s.current);
        countTo($("bestNum"), s.best);
        if (medalPrev !== null && s.current > medalPrev) {
            const m = $("medal"); m.classList.remove("pop"); void m.offsetWidth; m.classList.add("pop");
        }
        medalPrev = s.current;

        const t = stats(today);
        let msg;
        if (!routines.length) msg = "Build a routine to start your streak.";
        else if (t.due && t.done === t.due) msg = "Everything checked in today. Lovely work!";
        else if (t.due && t.done) msg = `${t.due - t.done} left today. You're nearly there.`;
        else if (t.due) msg = s.current ? `Check in today to keep your ${s.current}-day streak alive.` : "Check in today to start a new streak.";
        else msg = "Rest day today. Your streak is safe.";
        $("heroMsg").textContent = msg;

        const box = $("milestone");
        const goal = MILESTONES.find((g) => g > s.current);
        if (!goal || !s.current) { box.hidden = true; return; }
        box.hidden = false;
        const prev = [...MILESTONES].reverse().find((g) => g <= s.current) || 0;
        const pct = Math.min(100, Math.max(4, ((s.current - prev) / (goal - prev)) * 100));
        $("msLabel").textContent = `Next reward: ${goal}-day streak`;
        $("msCount").textContent = `${s.current} / ${goal}`;
        $("msFill").style.width = pct + "%";
        $("msLeaf").style.left = pct + "%";
    };

    // ---------- checklist ----------
    const renderStrip = () => {
        const strip = $("dayStrip");
        clear(strip);
        for (let i = WINDOW - 1; i >= 0; i--) {
            const d = addDays(today, -i), k = iso(d), st = stats(d);
            let cls = "dday";
            if (!st.due) cls += " is-rest";
            else if (st.done >= st.due) cls += " full";
            else if (st.done) cls += " part";
            else if (i > 0) cls += " miss";
            if (k === state.sel) cls += " is-sel";
            const b = el("button", cls);
            b.type = "button";
            b.setAttribute("aria-pressed", String(k === state.sel));
            b.setAttribute("aria-label", `${DOW[wk(d)]} ${d.getDate()}${i === 0 ? ", today" : ""}`);
            b.appendChild(el("span", null, i === 0 ? "Today" : DOW[wk(d)]));
            b.appendChild(el("b", null, String(d.getDate())));
            b.addEventListener("click", () => { state.sel = k; renderChecklist(); renderCal(); });
            strip.appendChild(b);
        }
    };

    const stepRow = (r, step, idx, day, set) => {
        const lab = el("label", "step tone-" + (r.type === "morning" ? "sun" : r.type === "afternoon" ? "sky" : "lav"));
        const cb = el("input");
        cb.type = "checkbox";
        cb.checked = set.has(idx);
        cb.addEventListener("change", () => onStep(r, idx, cb.checked, day));
        lab.appendChild(cb);
        const box = el("span", "step__box");
        box.appendChild(svgUse("ic-check"));
        lab.appendChild(box);
        if (step.image) {
            const th = el("span", "step__thumb");
            const im = el("img");
            im.src = step.image; im.alt = ""; im.loading = "lazy";
            th.appendChild(im);
            lab.appendChild(th);
        }
        const tx = el("span", "step__text");
        tx.appendChild(el("b", null, step.name));
        if (step.product) tx.appendChild(el("em", null, step.product));
        lab.appendChild(tx);
        return lab;
    };

    const trkCard = (r, day, k) => {
        const done = doneSet(day).has(r.id);
        const set = getSteps(k, r.id);
        const total = r.steps.length;
        const ticked = done ? total : Math.min(set.size, total);
        const card = el("article", "trk" + (done ? " is-done" : ""));
        card.dataset.id = r.id;

        const head = el("div", "trk__head");
        const chk = el("button", "trk__check");
        chk.type = "button";
        chk.setAttribute("aria-pressed", String(done));
        chk.setAttribute("aria-label", `${done ? "Undo" : "Check in"} ${r.name}`);
        chk.appendChild(svgUse("ic-check"));
        chk.addEventListener("click", () => setDone(r, k, !done, chk));
        head.appendChild(chk);

        const title = el("div", "trk__title");
        title.appendChild(el("h3", null, r.name));
        title.appendChild(el("span", "chip " + (r.type === "morning" ? "chip--sun" : r.type === "afternoon" ? "chip--sky" : "chip--lav"), r.type));
        title.appendChild(el("span", "trk__time", r.time));
        if (total) title.appendChild(el("span", "trk__time", `${ticked}/${total} steps`));
        head.appendChild(title);

        if (total) {
            const tg = el("button", "trk__toggle");
            tg.type = "button";
            const open = state.open.has(r.id);
            tg.setAttribute("aria-expanded", String(open));
            tg.setAttribute("aria-label", `${open ? "Hide" : "Show"} steps for ${r.name}`);
            tg.appendChild(svgUse("ic-arrow-l"));
            tg.addEventListener("click", () => { open ? state.open.delete(r.id) : state.open.add(r.id); renderList(); });
            head.appendChild(tg);
        }
        card.appendChild(head);

        if (total) {
            const m = el("div", "trk__meter");
            const f = el("i");
            f.style.width = (100 * ticked / total) + "%";
            m.appendChild(f);
            card.appendChild(m);
            const ul = el("ul", "trk__steps");
            ul.hidden = !state.open.has(r.id);
            r.steps.forEach((s, i) => {
                const li = el("li");
                li.appendChild(stepRow(r, s, i, k, done ? new Set(r.steps.map((_, j) => j)) : set));
                ul.appendChild(li);
            });
            card.appendChild(ul);
        }
        return card;
    };

    const renderList = () => {
        const day = parse(state.sel), list = $("dayList");
        clear(list);
        const due = dueList(day);
        $("dayRest").hidden = due.length > 0;
        due.sort((a, b) => a.time.localeCompare(b.time)).forEach((r) => list.appendChild(trkCard(r, day, state.sel)));
    };

    const renderChecklist = () => {
        renderStrip();
        const day = parse(state.sel), st = stats(day);
        const isToday = state.sel === todayIso;
        const label = isToday ? "Today" : `${DOW[wk(day)]} ${day.getDate()} ${MONTHS[day.getMonth()].slice(0, 3)}`;
        const note = $("dayNote");
        clear(note);
        note.appendChild(el("b", null, label));
        note.appendChild(document.createTextNode(isToday ? "" : " · catching up on a past day"));
        $("dayChip").textContent = `${st.done}/${st.due}`;
        const pct = st.due ? (100 * st.done / st.due) : 0;
        $("dayFill").style.width = pct + "%";
        $("dayLeaf").style.left = pct + "%";
        const complete = st.due > 0 && st.done === st.due;
        $("dayDone").hidden = !complete;
        $("dayDoneMsg").textContent = complete ? (isToday ? "You finished every routine today." : "Every routine on this day is checked in.") : "";
        renderList();
    };

    // ---------- saving ----------
    const save = async (r, k, done) => {
        const key = k + ":" + r.id;
        if (state.busy.has(key)) return;
        state.busy.add(key);
        const before = state.logs[k] ? new Set(state.logs[k]) : null;
        const ids = new Set(state.logs[k] || []);
        done ? ids.add(r.id) : ids.delete(r.id);
        state.logs[k] = ids;
        refresh();
        try {
            const body = new URLSearchParams({ routine: r.id, date: k, done: done ? "1" : "0" });
            const res = await fetch(D.log_url, {
                method: "POST",
                headers: { "X-CSRFToken": cookie("csrftoken"), "X-Requested-With": "XMLHttpRequest" },
                body, credentials: "same-origin",
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok || !data.ok) throw new Error(data.error || "Couldn't save that. Try again.");
            state.logs[k] = new Set(data.done_ids);
            applySummary(data.summary);
        } catch (err) {
            if (before) state.logs[k] = before; else delete state.logs[k];
            toast(err.message || "Couldn't save that. Try again.");
        } finally {
            state.busy.delete(key);
            refresh();
        }
    };

    const setDone = (r, k, done, btn) => {
        const set = getSteps(k, r.id);
        if (done) { r.steps.forEach((_, i) => set.add(i)); burst(btn, 12); }
        else set.clear();
        setSteps(k, r.id, set);
        const before = stats(parse(k));
        save(r, k, done).then(() => {
            const after = stats(parse(k));
            if (done && after.due && after.done === after.due && before.done < before.due) {
                burst($("dayDone"), 28);
            }
        });
    };

    const onStep = (r, idx, on, k) => {
        const wasDone = doneSet(parse(k)).has(r.id);
        let set = getSteps(k, r.id);
        if (wasDone) set = new Set(r.steps.map((_, i) => i));
        on ? set.add(idx) : set.delete(idx);
        setSteps(k, r.id, set);
        if (set.size >= r.steps.length && !wasDone) {
            const btn = document.querySelector(`.trk[data-id="${r.id}"] .trk__check`);
            burst(btn, 12);
            save(r, k, true);
        } else if (wasDone && set.size < r.steps.length) {
            save(r, k, false);
        } else {
            renderList();
        }
    };

    // ---------- calendar ----------
    const earliest = () => routines.reduce((m, r) => (r.createdD < m ? r.createdD : m), today);
    const renderCal = () => {
        const y = state.calY, m = state.calM;
        $("calMonth").textContent = `${MONTHS[m]} ${y}`;
        const first = new Date(y, m, 1), days = new Date(y, m + 1, 0).getDate();
        const grid = $("calGrid");
        clear(grid);
        for (let i = 0; i < wk(first); i++) grid.appendChild(el("span", "cday cday--blank"));
        for (let n = 1; n <= days; n++) {
            const d = new Date(y, m, n), k = iso(d), st = stats(d);
            let cls = "cday";
            if (d > today) cls += " is-future";
            else if (!st.due) cls += " is-rest";
            else if (st.done >= st.due) cls += " is-full";
            else if (st.done) cls += " is-part";
            else if (k === todayIso) cls += " is-pending";
            else cls += " is-miss";
            if (k === todayIso) cls += " is-today";
            if (k === state.sel) cls += " is-sel";
            const b = el("button", cls, String(n));
            b.type = "button";
            b.setAttribute("aria-label", `${n} ${MONTHS[m]}: ${d > today ? "upcoming" : st.due ? `${st.done} of ${st.due} done` : "rest day"}`);
            b.addEventListener("click", () => pickDay(d));
            grid.appendChild(b);
        }
        $("calNext").disabled = y === today.getFullYear() && m === today.getMonth();
        const e = earliest();
        $("calPrev").disabled = y < e.getFullYear() || (y === e.getFullYear() && m <= e.getMonth());
    };

    const pickDay = (d) => {
        const k = iso(d), st = stats(d), det = $("calDetail");
        const name = `${DOW[wk(d)]} ${d.getDate()} ${MONTHS[d.getMonth()]}`;
        if (d > today) det.textContent = `${name}: coming up.`;
        else if (!st.due) det.textContent = `${name}: rest day, nothing scheduled.`;
        else {
            const ok = doneSet(d);
            const names = dueList(d).map((r) => `${ok.has(r.id) ? "✓" : "○"} ${r.name}`).join("  ·  ");
            det.textContent = `${name}: ${st.done}/${st.due} done. ${names}`;
        }
        if (inWindow(d)) { state.sel = k; renderChecklist(); }
        renderCal();
    };

    $("calPrev").addEventListener("click", () => { if (--state.calM < 0) { state.calM = 11; state.calY--; } renderCal(); });
    $("calNext").addEventListener("click", () => { if (++state.calM > 11) { state.calM = 0; state.calY++; } renderCal(); });

    // ---------- stats, badges, consistency ----------
    const renderStats = () => {
        const s = state.summary;
        [["donutWeek", s.week_pct], ["donutMonth", s.month_pct]].forEach(([id, v]) => {
            const d = $(id);
            d.style.setProperty("--p", v);
            countTo(d.querySelector("[data-n]"), v);
            d.setAttribute("role", "img");
            d.setAttribute("aria-label", v + " percent");
        });
        countTo($("statTotal"), s.total);
        countTo($("statBest"), s.best);
    };

    let knownBadges = new Set(state.summary.badges.filter((b) => b.unlocked).map((b) => b.key));
    let freshKey = null;
    const renderBadges = () => {
        const grid = $("badgeGrid");
        clear(grid);
        const list = state.summary.badges;
        $("badgeCount").textContent = `${list.filter((b) => b.unlocked).length} / ${list.length}`;
        list.forEach((b) => {
            const c = el("article", `bcard tone-${b.tone}` + (b.unlocked ? " is-on" : "") + (b.key === freshKey ? " is-new" : ""));
            c.appendChild(el("div", "bcard__emoji", b.emoji));
            c.appendChild(el("strong", null, b.title));
            c.appendChild(el("p", null, b.desc));
            if (!b.unlocked && b.goal > 1) {
                const bar = el("div", "bcard__bar"), f = el("i");
                f.style.width = (100 * b.value / b.goal) + "%";
                bar.appendChild(f);
                c.appendChild(bar);
                c.appendChild(el("small", null, `${b.value} / ${b.goal}`));
            } else if (b.unlocked) {
                c.appendChild(el("small", null, "Unlocked"));
            }
            grid.appendChild(c);
        });
    };

    const renderConsistency = () => {
        const box = $("consistList");
        clear(box);
        routines.forEach((r) => {
            let due = 0, done = 0;
            const dots = el("div", "cdots");
            for (let i = 29; i >= 0; i--) {
                const d = addDays(today, -i);
                const isDue = dueOn(r, d), ok = doneSet(d).has(r.id);
                if (isDue) { due++; if (ok) done++; }
                if (i < 14) {
                    const dot = el("i", !isDue ? "r" : ok ? "f" : i === 0 ? "" : "m");
                    dots.appendChild(dot);
                }
            }
            const pct = due ? Math.round(100 * done / due) : 0;
            const row = el("div", "crow");
            const left = el("div");
            left.appendChild(el("h3", null, r.name));
            left.appendChild(el("small", null, `${done} of ${due} days`));
            row.appendChild(left);
            const bar = el("div", "cbar"), f = el("i");
            f.style.width = pct + "%";
            bar.appendChild(f);
            row.appendChild(bar);
            row.appendChild(el("span", "cpct", pct + "%"));
            box.appendChild(row);
        });
    };

    // ---------- badge reveal ----------
    const applySummary = (s) => {
        const fresh = s.badges.filter((b) => b.unlocked && !knownBadges.has(b.key));
        state.summary = s;
        if (fresh.length) {
            fresh.forEach((b) => knownBadges.add(b.key));
            freshKey = fresh[0].key;
            const b = fresh[0], dlg = $("badgeDlg");
            $("bdEmoji").textContent = b.emoji;
            $("bdTitle").textContent = b.title;
            $("bdDesc").textContent = b.desc;
            dlg.className = "dlg tone-" + b.tone;
            if (dlg.showModal && !dlg.open) { try { dlg.showModal(); } catch (e) { /* ignore */ } }
            setTimeout(() => burst($("bdEmoji"), 30), 200);
        }
    };
    const dlg = $("badgeDlg");
    dlg.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", () => dlg.close()));
    dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });

    const refresh = () => {
        renderHero(); renderChecklist(); renderCal(); renderStats(); renderBadges(); renderConsistency();
    };

    if (routines.length) refresh(); else renderHero();
})();
