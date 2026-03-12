// StackForge Fintech App Logic
document.addEventListener('DOMContentLoaded', () => {
    console.log('Fintech Service Dashboard Initialized');
    initChart();
});

function initChart() {
    const ctx = document.getElementById('performanceChart').getContext('2d');
    
    // Gradient for chart
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Feb 02', 'Feb 03', 'Feb 04', 'Feb 05', 'Feb 06', 'Feb 07', 'Feb 08'],
            datasets: [{
                label: 'Portfolio Value ($)',
                data: [135000, 138000, 137500, 140000, 139000, 141000, 142500],
                borderColor: '#6366f1',
                borderWidth: 3,
                backgroundColor: gradient,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#9ca3af', font: { size: 10 } }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#9ca3af', font: { size: 10 } }
                }
            }
        }
    });
}

function showModal() {
    document.getElementById('transferModal').style.display = 'flex';
}

function hideModal() {
    document.getElementById('transferModal').style.display = 'none';
}

// Close modal on background click
window.onclick = (event) => {
    const modal = document.getElementById('transferModal');
    if (event.target == modal) {
        hideModal();
    }
}
