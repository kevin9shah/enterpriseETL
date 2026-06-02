document.addEventListener("DOMContentLoaded", () => {
    // API base URL (relative to serve port)
    const API_STATS = "/api/stats";
    const API_RATES = "/api/exchange-rates";
    const API_SALES = "/api/state-sales";
    const API_LOGS = "/api/logs";

    // Chart instances
    let ratesChart = null;
    let salesChart = null;

    // Check for local file browsing
    if (window.location.protocol === "file:") {
        const banner = document.getElementById("file-warning-banner");
        if (banner) banner.style.display = "flex";
    }

    // Fetch and populate stats
    function loadStats() {
        fetch(API_STATS)
            .then(res => res.json())
            .then(data => {
                document.getElementById("stat-orders").textContent = data.total_orders.toLocaleString();
                document.getElementById("stat-customers").textContent = data.total_customers.toLocaleString();
                
                // Format revenue as Currency (BRL/USD/INR depending on context, using generic format)
                document.getElementById("stat-revenue").textContent = "$" + data.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                
                const healthEl = document.getElementById("stat-health");
                const statusCard = document.getElementById("status-card");
                const statusIcon = document.getElementById("status-icon");

                healthEl.textContent = data.pipeline_health;

                if (data.pipeline_health === "Healthy") {
                    statusCard.style.borderColor = "var(--green)";
                    statusIcon.className = "card-icon green";
                    statusIcon.innerHTML = '<i class="fa-solid fa-circle-check"></i>';
                } else {
                    statusCard.style.borderColor = "var(--red)";
                    statusIcon.className = "card-icon red";
                    statusIcon.innerHTML = '<i class="fa-solid fa-circle-xmark"></i>';
                }
            })
            .catch(err => console.error("Error loading stats:", err));
    }

    // Fetch and render exchange rates chart
    function loadExchangeRates() {
        fetch(API_RATES)
            .then(res => res.json())
            .then(data => {
                if (typeof Chart === 'undefined') {
                    console.warn("Chart.js is not loaded. Skipping chart rendering.");
                    return;
                }
                const labels = Object.keys(data);
                const values = Object.values(data);

                const ctx = document.getElementById("rates-chart").getContext("2d");
                
                // Create gradient
                const gradient = ctx.createLinearGradient(0, 0, 0, 300);
                gradient.addColorStop(0, 'rgba(59, 130, 246, 0.4)');
                gradient.addColorStop(1, 'rgba(139, 92, 246, 0.0)');

                if (ratesChart) {
                    ratesChart.destroy();
                }

                ratesChart = new Chart(ctx, {
                    type: "line",
                    data: {
                        labels: labels,
                        datasets: [{
                            label: "Value relative to INR",
                            data: values,
                            borderColor: "#3B82F6",
                            borderWidth: 3,
                            backgroundColor: gradient,
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: "#8B5CF6",
                            pointBorderColor: "#F3F4F6",
                            pointHoverRadius: 7
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                padding: 12,
                                displayColors: false
                            }
                        },
                        scales: {
                            x: {
                                grid: { display: false },
                                ticks: { color: "#9CA3AF" }
                            },
                            y: {
                                grid: { color: "#262D3D" },
                                ticks: { color: "#9CA3AF" }
                            }
                        }
                    }
                });
            })
            .catch(err => console.error("Error loading rates chart:", err));
    }

    // Fetch and render state sales chart
    function loadStateSales() {
        fetch(API_SALES)
            .then(res => res.json())
            .then(data => {
                if (typeof Chart === 'undefined') {
                    console.warn("Chart.js is not loaded. Skipping chart rendering.");
                    return;
                }
                const labels = data.map(item => item.state);
                const salesValues = data.map(item => item.sales);
                const tooltipCities = data.map(item => item.city);

                const ctx = document.getElementById("sales-chart").getContext("2d");

                const gradient = ctx.createLinearGradient(0, 0, 300, 0);
                gradient.addColorStop(0, '#06B6D4');
                gradient.addColorStop(1, '#3B82F6');

                if (salesChart) {
                    salesChart.destroy();
                }

                salesChart = new Chart(ctx, {
                    type: "bar",
                    data: {
                        labels: labels,
                        datasets: [{
                            data: salesValues,
                            backgroundColor: gradient,
                            borderRadius: 6,
                            barThickness: 16
                        }]
                    },
                    options: {
                        indexAxis: "y",
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    title: (context) => tooltipCities[context[0].dataIndex],
                                    label: (context) => "$" + context.raw.toLocaleString()
                                }
                            }
                        },
                        scales: {
                            x: {
                                grid: { color: "#262D3D" },
                                ticks: {
                                    color: "#9CA3AF",
                                    callback: (value) => "$" + (value / 1000000) + "M"
                                }
                            },
                            y: {
                                grid: { display: false },
                                ticks: { color: "#9CA3AF" }
                            }
                        }
                    }
                });
            })
            .catch(err => console.error("Error loading state sales chart:", err));
    }

    // Fetch and show logs
    function loadLogs() {
        fetch(API_LOGS)
            .then(res => res.json())
            .then(data => {
                const container = document.getElementById("logs-container");
                container.innerHTML = ""; // Clear
                
                data.forEach(logLine => {
                    const item = document.createElement("div");
                    item.className = "log-item";
                    item.textContent = logLine;
                    container.appendChild(item);
                });
                
                // Scroll to bottom
                container.scrollTop = container.scrollHeight;
            })
            .catch(err => console.error("Error loading logs:", err));
    }

    // Handle pipeline manual trigger
    document.getElementById("run-pipeline-btn").addEventListener("click", () => {
        const btn = document.getElementById("run-pipeline-btn");
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running Ingestion...';
        
        // Call running api
        fetch("/api/run", { method: "POST" })
            .then(res => res.json())
            .then(result => {
                alert(result.message);
                // Poll logs and stats after run completes
                setTimeout(() => {
                    loadStats();
                    loadExchangeRates();
                    loadStateSales();
                    loadLogs();
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-play"></i> Trigger Pipeline';
                }, 5000);
            })
            .catch(err => {
                console.error("Error triggering pipeline:", err);
                alert("Failed to contact trigger endpoint.");
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-play"></i> Trigger Pipeline';
            });
    });

    // Initial load
    loadStats();
    loadExchangeRates();
    loadStateSales();
    loadLogs();

    // Auto-refresh stats and logs every 10 seconds
    setInterval(() => {
        loadStats();
        loadLogs();
    }, 10000);
});
