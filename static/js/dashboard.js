// Dashboard chart — single-colour horizontal bar chart of category averages.
(function () {
    var el = document.getElementById('chart-data');
    var canvas = document.getElementById('categoryChart');
    if (!el || !canvas || typeof Chart === 'undefined') {
        return;
    }

    var data = {};
    try {
        data = JSON.parse(el.textContent);
    } catch (e) {
        return;
    }

    var labels = Object.keys(data);
    var values = labels.map(function (k) { return data[k]; });

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Average rating (out of 5)',
                data: values,
                backgroundColor: '#2563EB',
                borderRadius: 4,
                barThickness: 20
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (ctx) { return ctx.parsed.x.toFixed(2) + ' / 5'; }
                    }
                }
            },
            scales: {
                x: {
                    min: 0,
                    max: 5,
                    ticks: { stepSize: 1 },
                    grid: { color: '#EEEEEE' }
                },
                y: {
                    grid: { display: false }
                }
            }
        }
    });
})();