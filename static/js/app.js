(function (FV) {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function toast(message, type) {
        let region = document.getElementById('toastRegion');
        if (!region) {
            region = document.createElement('div');
            region.id = 'toastRegion';
            region.className = 'toast-region';
            region.setAttribute('aria-live', 'polite');
            document.body.appendChild(region);
        }
        const el = document.createElement('div');
        el.className = 'toast toast--' + (type || 'success');
        el.setAttribute('role', type === 'error' ? 'alert' : 'status');

        const icon = document.createElement('span');
        icon.textContent = type === 'error' ? '⚠️' : type === 'info' ? '💡' : '✅';
        icon.setAttribute('aria-hidden', 'true');

        const text = document.createElement('span');
        text.className = 'toast__msg';
        text.textContent = message;

        const close = document.createElement('button');
        close.type = 'button';
        close.className = 'toast__close';
        close.setAttribute('aria-label', 'Dismiss notification');
        close.textContent = '×';

        el.append(icon, text, close);
        region.appendChild(el);

        let timer = null;
        function dismiss() {
            clearTimeout(timer);
            if (!el.isConnected) return;
            el.classList.add('is-leaving');
            setTimeout(function () { el.remove(); }, 250);
        }
        close.addEventListener('click', dismiss);
        timer = setTimeout(dismiss, 4000);
        while (region.children.length > 4) region.firstElementChild.remove();
        return dismiss;
    }
    FV.toast = toast;

    function initDrawer() {
        const toggle = document.getElementById('navToggle');
        const drawer = document.getElementById('navDrawer');
        const overlay = document.getElementById('drawerOverlay');
        const closeBtn = document.getElementById('drawerClose');
        if (!toggle || !drawer || !overlay) return;

        function setOpen(open) {
            drawer.classList.toggle('is-open', open);
            drawer.setAttribute('aria-hidden', String(!open));
            toggle.setAttribute('aria-expanded', String(open));
            toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
            document.body.classList.toggle('drawer-open', open);
            if (open) {
                overlay.hidden = false;
                requestAnimationFrame(function () { overlay.classList.add('is-open'); });
                closeBtn.focus();
            } else {
                overlay.classList.remove('is-open');
                setTimeout(function () { if (!drawer.classList.contains('is-open')) overlay.hidden = true; }, 250);
            }
        }

        toggle.addEventListener('click', function () { setOpen(!drawer.classList.contains('is-open')); });
        closeBtn.addEventListener('click', function () { setOpen(false); toggle.focus(); });
        overlay.addEventListener('click', function () { setOpen(false); });
        drawer.addEventListener('click', function (e) { if (e.target.closest('a')) setOpen(false); });

        document.addEventListener('keydown', function (e) {
            if (!drawer.classList.contains('is-open')) return;
            if (e.key === 'Escape') {
                setOpen(false);
                toggle.focus();
                return;
            }
            if (e.key !== 'Tab') return;
            const focusable = drawer.querySelectorAll('a[href], button:not([disabled])');
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (e.shiftKey && document.activeElement === first) {
                e.preventDefault();
                last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        });

        window.matchMedia('(min-width: 901px)').addEventListener('change', function (e) {
            if (e.matches && drawer.classList.contains('is-open')) setOpen(false);
        });
    }

    function initDropdowns() {
        const dropdowns = document.querySelectorAll('[data-dropdown]');

        function close(dd, returnFocus) {
            const trigger = dd.querySelector('[data-dropdown-trigger]');
            const panel = dd.querySelector('[data-dropdown-panel]');
            if (panel.hidden) return;
            panel.hidden = true;
            trigger.setAttribute('aria-expanded', 'false');
            if (returnFocus) trigger.focus();
        }

        dropdowns.forEach(function (dd) {
            const trigger = dd.querySelector('[data-dropdown-trigger]');
            const panel = dd.querySelector('[data-dropdown-panel]');
            trigger.addEventListener('click', function () {
                const willOpen = panel.hidden;
                dropdowns.forEach(function (other) { close(other, false); });
                panel.hidden = !willOpen;
                trigger.setAttribute('aria-expanded', String(willOpen));
            });
            panel.addEventListener('click', function (e) {
                if (e.target.closest('a, [data-close-dropdown]')) close(dd, false);
            });
        });

        document.addEventListener('click', function (e) {
            dropdowns.forEach(function (dd) { if (!dd.contains(e.target)) close(dd, false); });
        });
        document.addEventListener('keydown', function (e) {
            if (e.key !== 'Escape') return;
            dropdowns.forEach(function (dd) { close(dd, true); });
        });
    }

    function initNotifications() {
        const list = document.getElementById('notifList');
        const badge = document.getElementById('notifBadge');
        const markAll = document.getElementById('markAllRead');
        if (!list || !badge) return;

        function render() {
            const items = FV.store.getNotifications();
            const unread = items.filter(function (n) { return !n.read; }).length;
            badge.hidden = unread === 0;
            badge.textContent = unread;
            if (markAll) markAll.hidden = unread === 0;
            list.innerHTML = '';
            if (!items.length) {
                const empty = document.createElement('li');
                empty.className = 'notif-empty';
                empty.textContent = "You're all caught up.";
                list.appendChild(empty);
                return;
            }
            items.forEach(function (n) {
                const li = document.createElement('li');
                li.className = 'notif-item' + (n.read ? '' : ' is-unread');
                const dot = document.createElement('i');
                dot.className = 'dot';
                const body = document.createElement('div');
                const title = document.createElement('strong');
                title.textContent = n.title;
                const text = document.createElement('span');
                text.textContent = n.body + ' · ' + n.time;
                body.append(title, text);
                li.append(dot, body);
                list.appendChild(li);
            });
        }

        if (markAll) {
            markAll.addEventListener('click', function () {
                FV.store.markAllRead();
                render();
                toast('All notifications marked as read', 'info');
            });
        }
        render();
    }

    function initIdentity() {
        const settings = FV.store.getSettings();
        const name = settings.name.trim();
        document.querySelectorAll('[data-user-name]').forEach(function (el) { el.textContent = name || 'Friend'; });
        document.querySelectorAll('[data-avatar]').forEach(function (el) { el.textContent = (name || 'F').charAt(0).toUpperCase(); });
        const page = document.body.dataset.page;
        document.querySelectorAll('[data-nav]').forEach(function (link) {
            if (link.dataset.nav === page) link.setAttribute('aria-current', 'page');
        });
        document.querySelectorAll('[data-logout]').forEach(function (btn) {
            btn.addEventListener('click', function () { toast('Logged out — see you soon!', 'info'); });
        });
    }

    function initEffects() {
        if (reduceMotion) return;
        let active = null;
        document.addEventListener('pointermove', function (e) {
            if (e.pointerType === 'touch') return;
            const el = e.target.closest ? e.target.closest('.tilt') : null;
            if (active && active !== el) active.style.transform = '';
            active = el;
            if (!el) return;
            const r = el.getBoundingClientRect();
            const x = (e.clientX - r.left) / r.width - 0.5;
            const y = (e.clientY - r.top) / r.height - 0.5;
            el.style.transform = 'perspective(800px) rotateX(' + (-y * 5) + 'deg) rotateY(' + (x * 5) + 'deg) translateY(-3px)';
        });
        document.addEventListener('pointerleave', function () {
            if (active) active.style.transform = '';
            active = null;
        });

        const colors = ['#4d8dff', '#ffd84d', '#7fdcb5', '#b9a8ff'];
        document.addEventListener('click', function (e) {
            if (!e.target.closest('.btn, .tile')) return;
            for (let i = 0; i < 9; i++) {
                const s = document.createElement('span');
                const angle = (Math.PI * 2 * i) / 9;
                const dist = 30 + Math.random() * 25;
                s.className = 'spark';
                s.style.left = e.clientX + 'px';
                s.style.top = e.clientY + 'px';
                s.style.background = colors[i % colors.length];
                s.style.setProperty('--dx', Math.cos(angle) * dist + 'px');
                s.style.setProperty('--dy', Math.sin(angle) * dist + 'px');
                document.body.appendChild(s);
                setTimeout(function () { s.remove(); }, 650);
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        initIdentity();
        initDrawer();
        initDropdowns();
        initNotifications();
        initEffects();
        const flash = FV.store.takeFlash();
        if (flash) toast(flash.message, flash.type);
    });
})(window.FV);
