// Toggle login/logout button
let isLoggedIn = false; // Change this based on user authentication status

const authBtn = document.getElementById('auth-btn');

authBtn.addEventListener('click', function () {
    isLoggedIn = !isLoggedIn; // Toggle login state
    if (isLoggedIn) {
        authBtn.textContent = 'Logout';
        // Handle the login process (e.g., redirect, show user info, etc.)
    } else {
        authBtn.textContent = 'Login';
        // Handle logout process (e.g., clear session, redirect, etc.)
    }
});
