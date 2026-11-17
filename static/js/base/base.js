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
})();
