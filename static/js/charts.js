// Função para inicializar os gráficos do Dashboard
function initDashboardCharts() {
    console.log("Iniciando gráficos do dashboard");

    // Gráfico de Status das Ordens de Serviço
    const serviceOrderStatusChart = document.getElementById('serviceOrderStatusChart');
    if (serviceOrderStatusChart) {
        fetch('/dashboard/service-order-stats')
            .then(response => response.json())
            .then(data => {
                new Chart(serviceOrderStatusChart, {
                    type: 'pie',
                    data: {
                        labels: ['Abertas', 'Em Progresso', 'Concluídas', 'Canceladas'],
                        datasets: [{
                            data: [
                                data.open,
                                data.in_progress,
                                data.completed,
                                data.cancelled
                            ],
                            backgroundColor: [
                                '#17a2b8', // info (azul) - abertas
                                '#0a6ebd', // primary (azul escuro) - em progresso
                                '#28a745', // success (verde) - concluídas
                                '#dc3545'  // danger (vermelho) - canceladas
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        aspectRatio: 1.5,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const label = context.label || '';
                                        const value = context.raw || 0;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = Math.round((value / total) * 100);
                                        return `${label}: ${value} (${percentage}%)`;
                                    }
                                }
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Erro ao carregar estatísticas de ordens de serviço:', error));
    }

    // Gráfico de Status dos Projetos
    const projectStatusChart = document.getElementById('projectStatusChart');
    if (projectStatusChart) {
        fetch('/dashboard/project-stats')
            .then(response => response.json())
            .then(data => {
                new Chart(projectStatusChart, {
                    type: 'pie',
                    data: {
                        labels: ['Planejamento', 'Em Progresso', 'Em Espera', 'Concluídos', 'Cancelados'],
                        datasets: [{
                            data: [
                                data.planning,
                                data.in_progress,
                                data.on_hold,
                                data.completed,
                                data.cancelled
                            ],
                            backgroundColor: [
                                '#17a2b8', // info (azul) - planejamento
                                '#0a6ebd', // primary (azul escuro) - em progresso
                                '#ffc107', // warning (amarelo) - em espera
                                '#28a745', // success (verde) - concluídos
                                '#dc3545'  // danger (vermelho) - cancelados
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        aspectRatio: 1.5,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const label = context.label || '';
                                        const value = context.raw || 0;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = Math.round((value / total) * 100);
                                        return `${label}: ${value} (${percentage}%)`;
                                    }
                                }
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Erro ao carregar estatísticas de projetos:', error));
    }

    // Gráfico de status do estoque
    const inventoryStatusChart = document.getElementById('inventoryStatusChart');
    if (inventoryStatusChart) {
        // Inventory Status Chart
        fetch('/stock/stats')
            .then(response => response.json())
            .then(data => {
                new Chart(inventoryStatusChart, {
                    type: 'pie',
                    data: {
                        labels: ['Estoque Normal', 'Estoque Baixo', 'Sem Estoque'],
                        datasets: [{
                            data: [data.normal, data.low, data.out],
                            backgroundColor: [
                                '#28a745', // success (verde) - normal
                                '#ffc107', // warning (amarelo) - baixo
                                '#dc3545'  // danger (vermelho) - sem estoque
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        aspectRatio: 1.5,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const label = context.label || '';
                                        const value = context.raw || 0;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = Math.round((value / total) * 100);
                                        return `${label}: ${value} (${percentage}%)`;
                                    }
                                }
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Erro ao carregar estatísticas de estoque:', error));
    }

    // Gráfico de itens mais populares do estoque
    const topItemsChart = document.getElementById('topItemsChart');
    if (topItemsChart) {
        // Top Items Chart
        fetch('/stock/top-items')
            .then(response => response.json())
            .then(data => {
                new Chart(topItemsChart, {
                    type: 'bar',
                    data: {
                        labels: data.items,
                        datasets: [{
                            label: 'Quantidade em Estoque',
                            data: data.quantities,
                            backgroundColor: '#0a6ebd',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        aspectRatio: 1.5,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        },
                        plugins: {
                            legend: {
                                display: false
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Erro ao carregar itens de maior quantidade:', error));
    }

    // Gráfico de Finanças Mensais para o Dashboard
    const monthlyFinanceChart = document.getElementById('monthlyFinanceChart');
    if (monthlyFinanceChart) {
        fetch('/dashboard/finance-stats')
            .then(response => response.json())
            .then(data => {
                new Chart(monthlyFinanceChart, {
                    type: 'line',
                    data: {
                        labels: data.months,
                        datasets: [
                            {
                                label: 'Receitas',
                                data: data.income,
                                borderColor: '#28a745',
                                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                                tension: 0.1,
                                fill: true
                            },
                            {
                                label: 'Despesas',
                                data: data.expenses,
                                borderColor: '#dc3545',
                                backgroundColor: 'rgba(220, 53, 69, 0.1)',
                                tension: 0.1,
                                fill: true
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        aspectRatio: 1.5,
                        scales: {
                            y: {
                                ticks: {
                                    callback: function(value) {
                                        return 'R$ ' + value.toLocaleString('pt-BR');
                                    }
                                }
                            }
                        },
                        plugins: {
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return context.dataset.label + ': R$ ' + context.parsed.y.toLocaleString('pt-BR');
                                    }
                                }
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Erro ao carregar estatísticas financeiras:', error));
    }
}

// Função para inicializar os gráficos da página de Finanças
function initFinanceCharts() {
    console.log("Inicializando gráficos de finanças");

    // Gráfico de Receitas vs Despesas
    const incomeExpenseChart = document.getElementById('incomeExpenseChart');
    if (incomeExpenseChart) {
        fetch('/finance/stats')
            .then(response => response.json())
            .then(data => {
                new Chart(incomeExpenseChart, {
                    type: 'pie',
                    data: {
                        labels: ['Receitas', 'Despesas'],
                        datasets: [{
                            data: [data.income, data.expenses],
                            backgroundColor: [
                                '#28a745', // success (verde) - receitas
                                '#dc3545'  // danger (vermelho) - despesas
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        aspectRatio: 1.5,
                        plugins: {
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const label = context.label || '';
                                        const value = context.raw || 0;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = Math.round((value / total) * 100);
                                        return `${label}: R$ ${value.toLocaleString('pt-BR')} (${percentage}%)`;
                                    }
                                }
                            },
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Erro ao carregar dados financeiros:', error));
    }

    // Gráfico de Top Categorias
    const categoriesChart = document.getElementById('categoriesChart');
    if (categoriesChart) {
        fetch('/finance/category-stats')
            .then(response => response.json())
            .then(data => {
                new Chart(categoriesChart, {
                    type: 'bar',
                    data: {
                        labels: data.categories,
                        datasets: [{
                            label: 'Valor',
                            data: data.values,
                            backgroundColor: data.colors,
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        aspectRatio: 1.5,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    callback: function(value) {
                                        return 'R$ ' + value.toLocaleString('pt-BR');
                                    }
                                }
                            }
                        },
                        plugins: {
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return context.dataset.label + ': R$ ' + context.parsed.y.toLocaleString('pt-BR');
                                    }
                                }
                            },
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Erro ao carregar dados de categorias:', error));
    }
}

// Inicializar gráficos quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM carregado, verificando gráficos para inicializar");

    // Configurar botões da página de segurança
    if (document.getElementById('backup-btn')) {
        document.getElementById('backup-btn').addEventListener('click', function() {
            // Simular backup
            fetch('/security/backup', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Backup realizado com sucesso!');
                } else {
                    alert('Erro ao realizar backup: ' + data.message);
                }
            });
        });
    }

    if (document.getElementById('log-btn')) {
        document.getElementById('log-btn').addEventListener('click', function() {
            fetch('/security/logs')
            .then(response => response.json())
            .then(data => {
                alert('Logs do sistema:\n\n' + data.logs.join('\n'));
            });
        });
    }

    if (document.getElementById('security-scan') || document.getElementById('check-security-btn')) {
        const scanButton = document.getElementById('security-scan') || document.getElementById('check-security-btn');
        scanButton.addEventListener('click', function() {
            fetch('/security/scan', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                let message = 'Resultados da verificação de segurança:\n\n';
                data.results.forEach(result => {
                    message += `[${result.status.toUpperCase()}] ${result.message}\n`;
                });
                alert(message);
            });
        });
    }

    // Inicializa gráficos do dashboard se estiverem presentes
    if (document.getElementById('serviceOrderStatusChart') || 
        document.getElementById('projectStatusChart') || 
        document.getElementById('monthlyFinanceChart') ||
        document.getElementById('inventoryStatusChart') ||
        document.getElementById('topItemsChart')) {
        initDashboardCharts();
    }

    // Inicializa gráficos na página de finanças se presentes
    if (document.getElementById('incomeExpenseChart') || document.getElementById('categoriesChart')) {
        console.log("Inicializando gráficos de finanças");
        initFinanceCharts();
    }
});