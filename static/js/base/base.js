(function () {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    // Cards lean toward the pointer
    document.querySelectorAll('.tilt').forEach(function (el) {
        el.addEventListener('pointermove', function (e) {
            const r = el.getBoundingClientRect();
            const x = (e.clientX - r.left) / r.width - 0.5;
            const y = (e.clientY - r.top) / r.height - 0.5;
            el.style.transform =
                'perspective(800px) rotateX(' + (-y * 5) + 'deg) rotateY(' + (x * 5) + 'deg) translateY(-3px)';
        });
        el.addEventListener('pointerleave', function () {
            el.style.transform = '';
        });
    });

    // Little confetti burst when pressing buttons
    const colors = ['#4d8dff', '#ffd84d', '#7fdcb5', '#b9a8ff'];
    document.addEventListener('click', function (e) {
        if (!e.target.closest('button, .btn, .tile')) return;
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
})();
