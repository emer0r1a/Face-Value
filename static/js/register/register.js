document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('registerForm');
    if (!form) return;

    var pw = document.getElementById('password');
    var confirm = document.getElementById('confirm_password');
    var bar = document.getElementById('pwBar');
    var label = document.getElementById('pwLabel');
    var leaf = form.querySelector('.grow svg');
    var hint = document.getElementById('matchHint');

    document.querySelectorAll('[data-toggle-pw]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var input = document.getElementById(btn.dataset.togglePw);
            var show = input.type === 'password';
            input.type = show ? 'text' : 'password';
            btn.textContent = show ? 'Hide' : 'Show';
        });
    });

    // The leaf "grows" as the password gets stronger
    var stages = [
        { t: 'Plant a seed', c: '#c9d6b5' },
        { t: 'Sprouting', c: '#d9a441' },
        { t: 'Growing', c: '#a4b83a' },
        { t: 'Thriving', c: '#76A032' },
        { t: 'In full bloom', c: '#4d6f1c' }
    ];
    function score(v) {
        if (!v) return 0;
        var s = 0;
        if (v.length >= 8) s++;
        if (v.length >= 12) s++;
        if (/[a-z]/.test(v) && /[A-Z]/.test(v)) s++;
        if (/\d/.test(v) && /[^A-Za-z0-9]/.test(v)) s++;
        return Math.min(s, 4);
    }
    function paint() {
        var s = score(pw.value);
        bar.style.width = (pw.value ? 12 + s * 22 : 0) + '%';
        bar.style.background = stages[s].c;
        label.textContent = stages[s].t;
        leaf.style.transform = 'scale(' + (0.7 + s * 0.2) + ') rotate(' + (-20 + s * 5) + 'deg)';
        leaf.style.color = stages[s].c;
        checkMatch();
    }
    function checkMatch() {
        if (!confirm.value) { hint.textContent = ''; hint.className = 'field-hint'; return; }
        var ok = pw.value === confirm.value;
        hint.textContent = ok ? 'Passwords match' : "Passwords don't match yet";
        hint.className = 'field-hint ' + (ok ? 'good' : 'bad');
    }
    pw.addEventListener('input', paint);
    confirm.addEventListener('input', checkMatch);

    form.addEventListener('submit', function (e) {
        var msg = '';
        if (pw.value.length < 8) msg = 'Password must be at least 8 characters long.';
        else if (pw.value !== confirm.value) msg = 'Passwords do not match.';
        if (!msg) return;
        e.preventDefault();
        var box = form.parentElement.querySelector('.error');
        if (!box) {
            box = document.createElement('div');
            box.className = 'error';
            box.setAttribute('role', 'alert');
            form.parentElement.insertBefore(box, form);
        }
        box.textContent = msg;
        (pw.value.length < 8 ? pw : confirm).focus();
    });
});
