
        document.addEventListener('DOMContentLoaded', function() {
            fetch('/api/tuition_stats')
                .then(response => response.json())
                .then(data => {
                    renderChart(data);
                });
        });

        function renderChart(data) {
            const ctx = document.getElementById('tuitionChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Tuition Payments (TSh)',
                        data: data.amounts,
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        