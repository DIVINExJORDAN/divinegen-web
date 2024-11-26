function updateUsageCharts(cpuUsage, ramUsage) {
    // Add new data points to CPU usage chart
    cpuUsageChart.data.datasets[0].data.push(cpuUsage);
    cpuUsageChart.data.labels.push(new Date().toLocaleTimeString());
    cpuUsageChart.update();

    // Add new data points to RAM usage chart
    ramUsageChart.data.datasets[0].data.push(ramUsage);
    ramUsageChart.data.labels.push(new Date().toLocaleTimeString());
    ramUsageChart.update();
}

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

