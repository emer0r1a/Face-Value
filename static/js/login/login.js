document.addEventListener('DOMContentLoaded', function () {
    // Show / hide password
    document.querySelectorAll('[data-toggle-pw]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var input = document.getElementById(btn.dataset.togglePw);
            var show = input.type === 'password';
            input.type = show ? 'text' : 'password';
            btn.textContent = show ? 'Hide' : 'Show';
        });
    });

    var form = document.getElementById('loginForm');
    if (!form) return;
    form.addEventListener('submit', function (e) {
        var u = form.username.value.trim();
        var p = form.password.value;
        if (u && p) return;
        e.preventDefault();
        var box = form.parentElement.querySelector('.error');
        if (!box) {
            box = document.createElement('div');
            box.className = 'error';
            box.setAttribute('role', 'alert');
            form.parentElement.insertBefore(box, form);
        }
        box.textContent = 'Please enter both your username and password.';
        (u ? form.password : form.username).focus();
    });
});
