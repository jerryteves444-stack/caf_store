document.addEventListener("DOMContentLoaded", function () {
    // Dark mode toggle (persisted in localStorage; fine here since this is
    // a real deployed app, not a sandboxed artifact preview).
    const root = document.documentElement;
    const toggleBtn = document.getElementById("darkModeToggle");
    const saved = localStorage.getItem("theme");
    if (saved) root.setAttribute("data-bs-theme", saved);

    if (toggleBtn) {
        toggleBtn.addEventListener("click", function () {
            const current = root.getAttribute("data-bs-theme");
            const next = current === "dark" ? "light" : "dark";
            root.setAttribute("data-bs-theme", next);
            localStorage.setItem("theme", next);
        });
    }

    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebar = document.getElementById("sidebar");
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener("click", () => sidebar.classList.toggle("show"));
    }
});
