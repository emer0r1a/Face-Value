(() => {
    "use strict";
    const $ = (id) => document.getElementById(id);

    // ---- dialogs ----
    document.querySelectorAll("[data-open]").forEach((b) => {
        b.addEventListener("click", () => { const d = $(b.dataset.open); if (d && d.showModal) d.showModal(); });
    });
    document.querySelectorAll("dialog").forEach((d) => {
        d.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", () => d.close()));
        d.addEventListener("click", (e) => { if (e.target === d) d.close(); });
        if (d.hasAttribute("data-autoopen") && d.showModal) d.showModal();
    });

    // ---- report: send to the chosen product's report endpoint ----
    const form = $("reportForm"), pick = $("rpProduct");
    if (form && pick) {
        form.addEventListener("submit", (e) => {
            if (!pick.value) { e.preventDefault(); pick.focus(); return; }
            form.action = form.dataset.url.replace(/0\/report\/$/, pick.value + "/report/");
        });
    }

    // ---- photo preview ----
    const file = $("profile_image"), prev = $("avaPreview"), hint = $("photoHint"), remove = $("removePhoto");
    const MAX = 5 * 1024 * 1024;
    if (file && prev) {
        file.addEventListener("change", () => {
            const f = file.files[0];
            if (!f) return;
            if (f.size > MAX || !/^image\//.test(f.type)) {
                file.value = "";
                hint.textContent = f.size > MAX ? "That photo is over 5 MB. Try a smaller one." : "Please choose an image file.";
                return;
            }
            const img = document.createElement("img");
            img.alt = "";
            img.src = URL.createObjectURL(f);
            prev.replaceChildren(img);
            hint.textContent = f.name;
            if (remove) remove.checked = false;
        });
    }

    // ---- bio counter ----
    const bio = $("bio"), count = $("bioCount");
    if (bio && count) bio.addEventListener("input", () => { count.textContent = bio.value.length; });
})();
