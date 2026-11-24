(function () {
    // Avatar dropdown
    var btn = document.getElementById('avatarBtn');
    var menu = document.getElementById('avatarMenu');
    if (btn && menu) {
        var close = function () { menu.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); };
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            var open = menu.classList.toggle('open');
            btn.setAttribute('aria-expanded', open ? 'true' : 'false');
        });
        document.addEventListener('click', function (e) { if (!menu.contains(e.target)) close(); });
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
    }

    // Navbar gets a touch more presence once you scroll
    var nav = document.getElementById('fvNav');
    if (nav) {
        var onScroll = function () { nav.style.boxShadow = window.scrollY > 8 ? '0 10px 30px rgba(34,48,24,.14)' : ''; };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.querySelectorAll('.reveal').forEach(function (el) { el.classList.add('in'); });
        return;
    }

    // Scroll reveal
    if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (en) {
                if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
            });
        }, { threshold: 0.04, rootMargin: "0px 0px -30px 0px" });
        document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });
    } else {
        document.querySelectorAll('.reveal').forEach(function (el) { el.classList.add('in'); });
    }

    // Cards lean toward the pointer
    document.querySelectorAll('.tilt').forEach(function (el) {
        el.addEventListener('pointermove', function (e) {
            var r = el.getBoundingClientRect();
            var x = (e.clientX - r.left) / r.width - 0.5;
            var y = (e.clientY - r.top) / r.height - 0.5;
            el.style.transform = 'perspective(900px) rotateX(' + (-y * 3) + 'deg) rotateY(' + (x * 3) + 'deg)';
        });
        el.addEventListener('pointerleave', function () { el.style.transform = ''; });
    });

    // Leaf burst; call FV.burst(x, y) from anywhere
    var colors = ['#76A032', '#9bc255', '#8fd0ea', '#f6e9b4'];
    function burst(x, y, n) {
        n = n || 9;
        for (var i = 0; i < n; i++) {
            var s = document.createElement('span');
            var angle = (Math.PI * 2 * i) / n;
            var dist = 30 + Math.random() * 30;
            s.className = 'spark';
            s.style.left = x + 'px';
            s.style.top = y + 'px';
            s.style.background = colors[i % colors.length];
            s.style.setProperty('--dx', Math.cos(angle) * dist + 'px');
            s.style.setProperty('--dy', Math.sin(angle) * dist + 'px');
            document.body.appendChild(s);
            setTimeout(function (el) { el.remove(); }, 700, s);
        }
    }
    window.FV = window.FV || {};
    window.FV.burst = burst;

    document.addEventListener('click', function (e) {
        if (e.target.closest('button[type="submit"], .btn')) burst(e.clientX, e.clientY);
    });

    // ── Live notification polling + toasts ──────────────────────────────
    var POLL_URL = '/notifications/poll/';
    var CSRF = (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
    var toastContainer = null;
    var lastPollTime = new Date().toISOString();
    var shownIds = {};

    function getToastContainer() {
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-tray';
            toastContainer.setAttribute('aria-live', 'polite');
            toastContainer.setAttribute('aria-atomic', 'false');
            document.body.appendChild(toastContainer);
        }
        return toastContainer;
    }

    function updateBell(count) {
        var bell = document.querySelector('.bell');
        if (!bell) return;
        var badge = bell.querySelector('.bell__count');
        if (count > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'bell__count';
                bell.appendChild(badge);
            }
            badge.textContent = count;
        } else {
            if (badge) badge.remove();
        }
    }

    function showToast(notif) {
        if (shownIds[notif.id]) return;
        shownIds[notif.id] = true;

        var tray = getToastContainer();
        var toast = document.createElement('div');
        toast.className = 'toast';
        toast.setAttribute('role', 'alert');
        toast.innerHTML =
            '<span class="toast__icon">' + (notif.icon || '🔔') + '</span>' +
            '<div class="toast__body">' +
                '<strong>' + notif.title + '</strong>' +
                '<p>' + notif.message.substring(0, 90) + (notif.message.length > 90 ? '…' : '') + '</p>' +
            '</div>' +
            '<button type="button" class="toast__close" aria-label="Dismiss">×</button>';

        if (notif.url) {
            toast.style.cursor = 'pointer';
            toast.addEventListener('click', function (e) {
                if (e.target.closest('.toast__close')) return;
                dismiss();
                window.location.href = notif.url;
            });
        }

        tray.appendChild(toast);
        // Animate in
        requestAnimationFrame(function () { toast.classList.add('toast--in'); });

        function dismiss() {
            toast.classList.remove('toast--in');
            toast.classList.add('toast--out');
            setTimeout(function () { toast.remove(); }, 350);
            // Mark read in background
            fetch('/notifications/' + notif.id + '/read/', {
                method: 'POST',
                headers: { 'X-CSRFToken': CSRF },
                keepalive: true   // still completes when the click navigates to another page
            });
        }

        toast.querySelector('.toast__close').addEventListener('click', function (e) {
            e.stopPropagation();
            dismiss();
        });

        // Auto-dismiss after 7 s
        var timer = setTimeout(dismiss, 7000);
        toast.addEventListener('mouseenter', function () { clearTimeout(timer); });
        toast.addEventListener('mouseleave', function () { timer = setTimeout(dismiss, 3000); });
    }

    function poll() {
        var url = POLL_URL + '?since=' + encodeURIComponent(lastPollTime);
        lastPollTime = new Date().toISOString();
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (data) {
                if (!data) return;
                updateBell(data.unread);
                (data.fresh || []).forEach(showToast);
            })
            .catch(function () {}); // silent fail
    }

    // Only poll when the user is authenticated (bell element is present)
    if (document.querySelector('.bell')) {
        setTimeout(poll, 5000);           // first poll after 5 s
        setInterval(poll, 30000);         // then every 30 s
        document.addEventListener('visibilitychange', function () {
            if (!document.hidden) poll(); // immediate poll on tab focus
        });
    }
    // ────────────────────────────────────────────────────────────────────
})();
