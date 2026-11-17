document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('addProductForm');
    if (!form) return;

    /* ---------- ingredient chips preview ---------- */
    var ta = document.getElementById('ingredients');
    var count = document.getElementById('ingredientCount');
    var prev = document.getElementById('ingredientPreview');
    function parse(t) {
        var seen = {}, out = [];
        t.split(/[,\n;]+/).forEach(function (n) {
            n = n.trim(); var k = n.toLowerCase();
            if (n && !seen[k]) { seen[k] = 1; out.push(n); }
        });
        return out;
    }
    function render() {
        var items = parse(ta.value);
        count.textContent = items.length + ' ingredient' + (items.length === 1 ? '' : 's');
        prev.textContent = '';
        items.slice(0, 40).forEach(function (n) {
            var c = document.createElement('span'); c.className = 'chip'; c.textContent = n; prev.appendChild(c);
        });
    }
    ta.addEventListener('input', render); render();

    /* ---------- photo picker with live preview ---------- */
    var input = document.getElementById('image');
    var dz = document.getElementById('dropzone');
    var box = document.getElementById('preview');
    var txt = document.getElementById('dzText');
    var remove = document.getElementById('removeImage');
    var MAX = 5 * 1024 * 1024;

    function showError(msg) {
        var e = form.querySelector('.message.error');
        if (!e) { e = document.createElement('div'); e.className = 'message error'; e.setAttribute('role', 'alert'); var card = form.querySelector('.form-card'); card.insertBefore(e, card.querySelector('.form-group')); }
        e.textContent = msg;
    }
    function setPhoto(file) {
        if (!file) return;
        if (!/^image\/(jpeg|png|webp|gif)$/.test(file.type)) { showError('Please choose a JPG, PNG, WebP or GIF photo.'); input.value = ''; return; }
        if (file.size > MAX) { showError('That photo is over 5 MB. Please pick a smaller one.'); input.value = ''; return; }
        var r = new FileReader();
        r.onload = function () {
            box.textContent = '';
            var img = document.createElement('img'); img.src = r.result; img.alt = 'Photo preview'; box.appendChild(img);
            box.classList.add('pop');
            setTimeout(function () { box.classList.remove('pop'); }, 400);
            txt.textContent = 'Change photo';
            if (remove) remove.checked = false;
        };
        r.readAsDataURL(file);
    }
    input.addEventListener('change', function () { setPhoto(input.files[0]); });
    ['dragenter', 'dragover'].forEach(function (ev) { dz.addEventListener(ev, function (e) { e.preventDefault(); dz.classList.add('drag'); }); });
    ['dragleave', 'drop'].forEach(function (ev) { dz.addEventListener(ev, function (e) { e.preventDefault(); dz.classList.remove('drag'); }); });
    dz.addEventListener('drop', function (e) {
        var f = e.dataTransfer.files[0]; if (!f) return;
        var dt = new DataTransfer(); dt.items.add(f); input.files = dt.files; setPhoto(f);
    });

    /* ---------- validation + submit state ---------- */
    form.addEventListener('submit', function (e) {
        var name = form.product_name, brand = form.brand;
        var bad = [name, brand].filter(function (f) { return !f.value.trim(); })[0];
        if (bad) { e.preventDefault(); showError('Please fill in the product name and brand.'); bad.focus(); return; }
        var btn = document.getElementById('submitBtn'); btn.disabled = true; btn.firstChild.textContent = 'Saving… ';
    });
});
