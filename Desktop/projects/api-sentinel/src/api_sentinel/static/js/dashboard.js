// API Sentinel Dashboard JavaScript

// Confirm delete actions
document.addEventListener('htmx:confirm', function(event) {
    if (!confirm(event.detail.question)) {
        event.preventDefault();
    }
});

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        document.querySelectorAll('.flash').forEach(function(el) {
            el.style.opacity = '0';
            el.style.transition = 'opacity 0.5s';
            setTimeout(function() { el.remove(); }, 500);
        });
    }, 5000);
});

// Handle form validation feedback
document.addEventListener('htmx:afterRequest', function(event) {
    if (event.detail.successful === false) {
        // Show error toast or highlight form fields
        console.log('Request failed:', event.detail);
    }
});

// Copy to clipboard helper
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // Could show a toast notification
        console.log('Copied to clipboard');
    });
}

// Theme toggle (if needed)
function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
}

// Initialize theme from localStorage
if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark-theme');
}