
document.addEventListener('DOMContentLoaded', function() {
    function setTheme(theme) {
        document.body.classList.remove('light-theme', 'dark-theme');
        document.body.classList.add(theme);
        localStorage.setItem('theme', theme);
        
        const icons = document.querySelectorAll('.theme-icon, .fa-moon, .fa-sun');
        icons.forEach(icon => {
            icon.classList.remove('fa-moon', 'fa-sun');
            icon.classList.add(theme === 'dark-theme' ? 'fa-sun' : 'fa-moon');
        });
    }

    // Set initial theme from localStorage or default to light
    const savedTheme = localStorage.getItem('theme') || 'light-theme';
    setTheme(savedTheme);

    // Add click handlers to all theme toggle buttons
    document.querySelectorAll('#theme-toggle, #header-theme-toggle, .theme-toggle').forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const newTheme = document.body.classList.contains('light-theme') ? 'dark-theme' : 'light-theme';
            setTheme(newTheme);
        });
    });
});
