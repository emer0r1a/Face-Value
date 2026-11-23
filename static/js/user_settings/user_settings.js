(() => {
    "use strict";
    const box = document.getElementById("dark_mode");
    if (!box) return;
    // Preview straight away; the server saves it when the form is submitted.
    const apply = () => {
        document.documentElement.setAttribute("data-theme", box.checked ? "dark" : "light");
        try {
            const s = JSON.parse(localStorage.getItem("fv-settings") || "{}");
            s.darkMode = box.checked;
            localStorage.setItem("fv-settings", JSON.stringify(s));
        } catch (e) { /* storage unavailable */ }
    };
    box.addEventListener("change", apply);
})();
