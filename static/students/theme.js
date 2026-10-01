// Light/dark mode toggle. Bootstrap 5.3+ switches its whole color
// scheme based on the `data-bs-theme` attribute on <html> - so all
// this script does is flip that attribute and remember the choice.
(function () {
    var root = document.documentElement;
    var themeBtn = document.getElementById('theme-toggle');

    if (!themeBtn) {
        return;
    }

    themeBtn.addEventListener('click', function () {
        var current = root.getAttribute('data-bs-theme') === 'dark' ? 'dark' : 'light';
        var next = current === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-bs-theme', next);
        try {
            localStorage.setItem('theme', next);
        } catch (err) {
            // localStorage can be unavailable (e.g. private browsing) - fail quietly.
        }
    });
})();
