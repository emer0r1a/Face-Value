document.addEventListener('DOMContentLoaded', function () {
    const FV = window.FV;

    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        const name = document.getElementById('full_name');
        const bio = document.getElementById('bio');
        const bioCount = document.getElementById('bioCount');
        const avatar = document.getElementById('profileAvatar');
        const heading = document.getElementById('profileName');
        const settings = FV.store.getSettings();
        name.value = settings.name;
        bio.value = settings.bio;

        function refresh() {
            const value = name.value.trim();
            avatar.textContent = (value || 'F').charAt(0).toUpperCase();
            heading.textContent = value || 'Friend';
            bioCount.textContent = bio.value.length + ' / ' + bio.getAttribute('maxlength');
        }
        name.addEventListener('input', refresh);
        bio.addEventListener('input', refresh);
        refresh();

        profileForm.addEventListener('submit', function (e) {
            e.preventDefault();
            FV.store.saveSettings({ name: name.value.trim(), bio: bio.value.trim() });
            document.querySelectorAll('[data-user-name]').forEach(function (el) { el.textContent = name.value.trim() || 'Friend'; });
            document.querySelectorAll('[data-avatar]').forEach(function (el) { el.textContent = (name.value.trim() || 'F').charAt(0).toUpperCase(); });
            FV.toast('Profile saved');
        });
    }

    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        const dark = document.getElementById('darkMode');
        const email = document.getElementById('emailNotifications');
        const settings = FV.store.getSettings();
        dark.checked = settings.darkMode;
        email.checked = settings.emailNotifications;

        dark.addEventListener('change', function () {
            document.documentElement.removeAttribute('data-theme');
            if (dark.checked) document.documentElement.setAttribute('data-theme', 'dark');
        });

        settingsForm.addEventListener('submit', function (e) {
            e.preventDefault();
            FV.store.saveSettings({ darkMode: dark.checked, emailNotifications: email.checked });
            FV.toast('Settings saved');
        });

        const reset = document.getElementById('resetDemo');
        if (reset) {
            reset.addEventListener('click', function () {
                FV.store.resetProducts();
                FV.toast('Sample products restored', 'info');
            });
        }
    }
});
