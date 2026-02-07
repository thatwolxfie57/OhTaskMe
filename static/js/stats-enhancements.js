/**
 * Statistics Dashboard Enhancements for OhTaskMe
 * Provides interactive charts, real-time updates, and enhanced analytics
 */

const StatsEnhancements = {
    // Configuration
    config: {
        charts: {
            productivity: null,
            xpProgress: null,
            taskCompletion: null,
            weeklyActivity: null
        },
        updateInterval: 30000, // 30 seconds
        animationDuration: 750,
        colors: {
            primary: '#007bff',
            success: '#28a745',
            warning: '#ffc107',
            danger: '#dc3545',
            info: '#17a2b8',
            gradient: ['#007bff', '#0056b3', '#003d82']
        }
    },

    // State management
    state: {
        isInitialized: false,
        updateTimer: null,
        lastUpdate: null,
        isUpdating: false
    },

    /**
     * Initialize statistics dashboard enhancements
     */
    init() {
        if (this.state.isInitialized) return;
        
        console.log('Initializing Statistics Dashboard Enhancements...');
        
        this.enhanceCharts();
        this.setupRealTimeUpdates();
        this.setupInteractiveElements();
        this.setupKeyboardShortcuts();
        this.setupExportFeatures();
        this.addInsightCards();
        
        this.state.isInitialized = true;
        console.log('Statistics Dashboard Enhancements initialized successfully');
    },

    /**
     * Enhance existing charts with interactive features
     */
    enhanceCharts() {
        this.enhanceProductivityChart();
        this.enhanceXPChart();
        this.createAdditionalCharts();
        this.addChartInteractions();
    },

    /**
     * Enhance productivity trends chart
     */
    enhanceProductivityChart() {
        const ctx = document.getElementById('productivityChart');
        if (!ctx) return;

        // Get existing chart instance
        const existingChart = Chart.getChart(ctx);
        if (existingChart) {
            this.config.charts.productivity = existingChart;
            this.addChartEnhancements(existingChart, 'productivity');
        }
    },

    /**
     * Enhance XP progress chart
     */
    enhanceXPChart() {
        const ctx = document.getElementById('xpChart');
        if (!ctx) return;

        // Get existing chart instance
        const existingChart = Chart.getChart(ctx);
        if (existingChart) {
            this.config.charts.xpProgress = existingChart;
            this.addChartEnhancements(existingChart, 'xp');
        }
    },

    /**
     * Create additional interactive charts
     */
    createAdditionalCharts() {
        this.createTaskCompletionChart();
        this.createWeeklyActivityChart();
        this.createTimeDistributionChart();
    },

    /**
     * Create task completion rate chart
     */
    createTaskCompletionChart() {
        const container = document.querySelector('.additional-charts');
        if (!container) {
            this.createChartsContainer();
        }

        const chartHTML = `
            <div class="col-md-6 mb-4">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">
                            <i class="fas fa-chart-pie me-2 text-info"></i>
                            Task Completion Rate
                        </h6>
                        <div class="btn-group btn-group-sm" role="group">
                            <button class="btn btn-outline-secondary active" data-period="7">7D</button>
                            <button class="btn btn-outline-secondary" data-period="30">30D</button>
                            <button class="btn btn-outline-secondary" data-period="90">90D</button>
                        </div>
                    </div>
                    <div class="card-body">
                        <canvas id="taskCompletionChart" width="400" height="200"></canvas>
                        <div class="chart-legend mt-3">
                            <div class="row text-center">
                                <div class="col-4">
                                    <div class="legend-item">
                                        <div class="legend-color bg-success"></div>
                                        <small>Completed</small>
                                        <div class="legend-value" id="completed-count">--</div>
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="legend-item">
                                        <div class="legend-color bg-warning"></div>
                                        <small>Pending</small>
                                        <div class="legend-value" id="pending-count">--</div>
                                    </div>
                                </div>
                                <div class="col-4">
                                    <div class="legend-item">
                                        <div class="legend-color bg-danger"></div>
                                        <small>Overdue</small>
                                        <div class="legend-value" id="overdue-count">--</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.querySelector('.additional-charts').insertAdjacentHTML('beforeend', chartHTML);
        
        // Initialize chart
        this.initTaskCompletionChart();
    },

    /**
     * Create weekly activity heatmap
     */
    createWeeklyActivityChart() {
        const chartHTML = `
            <div class="col-md-6 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="fas fa-calendar-week me-2 text-warning"></i>
                            Weekly Activity Heatmap
                        </h6>
                    </div>
                    <div class="card-body">
                        <canvas id="weeklyActivityChart" width="400" height="200"></canvas>
                        <div class="activity-scale mt-3">
                            <small class="text-muted">Less</small>
                            <div class="scale-colors">
                                <div class="scale-item level-0"></div>
                                <div class="scale-item level-1"></div>
                                <div class="scale-item level-2"></div>
                                <div class="scale-item level-3"></div>
                                <div class="scale-item level-4"></div>
                            </div>
                            <small class="text-muted">More</small>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.querySelector('.additional-charts').insertAdjacentHTML('beforeend', chartHTML);
        
        // Initialize chart
        this.initWeeklyActivityChart();
    },

    /**
     * Create time distribution chart
     */
    createTimeDistributionChart() {
        const chartHTML = `
            <div class="col-12 mb-4">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">
                            <i class="fas fa-clock me-2 text-primary"></i>
                            Time Distribution by Hour
                        </h6>
                        <button class="btn btn-outline-primary btn-sm" onclick="StatsEnhancements.refreshTimeDistribution()">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                    </div>
                    <div class="card-body">
                        <canvas id="timeDistributionChart" width="800" height="300"></canvas>
                        <div class="time-insights mt-3">
                            <div class="row">
                                <div class="col-md-3 text-center">
                                    <div class="insight-card">
                                        <div class="insight-value" id="peak-hour">--</div>
                                        <div class="insight-label">Peak Hour</div>
                                    </div>
                                </div>
                                <div class="col-md-3 text-center">
                                    <div class="insight-card">
                                        <div class="insight-value" id="avg-tasks">--</div>
                                        <div class="insight-label">Avg Tasks/Hour</div>
                                    </div>
                                </div>
                                <div class="col-md-3 text-center">
                                    <div class="insight-card">
                                        <div class="insight-value" id="most-productive">--</div>
                                        <div class="insight-label">Most Productive</div>
                                    </div>
                                </div>
                                <div class="col-md-3 text-center">
                                    <div class="insight-card">
                                        <div class="insight-value" id="completion-rate">--</div>
                                        <div class="insight-label">Completion Rate</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.querySelector('.additional-charts').insertAdjacentHTML('beforeend', chartHTML);
        
        // Initialize chart
        this.initTimeDistributionChart();
    },

    /**
     * Create container for additional charts
     */
    createChartsContainer() {
        const existingCharts = document.querySelector('.row').parentElement;
        const chartsHTML = `
            <div class="row additional-charts mt-4">
                <div class="col-12">
                    <h4 class="mb-3">
                        <i class="fas fa-chart-line me-2 text-primary"></i>
                        Advanced Analytics
                    </h4>
                </div>
            </div>
        `;
        
        existingCharts.insertAdjacentHTML('beforeend', chartsHTML);
    },

    /**
     * Initialize task completion chart
     */
    initTaskCompletionChart() {
        const ctx = document.getElementById('taskCompletionChart');
        if (!ctx) return;

        this.config.charts.taskCompletion = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'Pending', 'Overdue'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        this.config.colors.success,
                        this.config.colors.warning,
                        this.config.colors.danger
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: this.config.animationDuration
                },
                onHover: (event, activeElements) => {
                    event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
                }
            }
        });

        // Load initial data
        this.loadTaskCompletionData();
    },

    /**
     * Initialize weekly activity chart
     */
    initWeeklyActivityChart() {
        const ctx = document.getElementById('weeklyActivityChart');
        if (!ctx) return;

        // Create heatmap-style chart using Chart.js matrix
        this.config.charts.weeklyActivity = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Tasks Completed',
                    data: [0, 0, 0, 0, 0, 0, 0],
                    backgroundColor: this.config.colors.primary,
                    borderRadius: 4,
                    maxBarThickness: 40
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            display: false
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                animation: {
                    duration: this.config.animationDuration,
                    easing: 'easeOutQuart'
                }
            }
        });

        // Load initial data
        this.loadWeeklyActivityData();
    },

    /**
     * Initialize time distribution chart
     */
    initTimeDistributionChart() {
        const ctx = document.getElementById('timeDistributionChart');
        if (!ctx) return;

        const hours = Array.from({length: 24}, (_, i) => `${i.toString().padStart(2, '0')}:00`);

        this.config.charts.timeDistribution = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: hours,
                datasets: [{
                    label: 'Tasks Completed',
                    data: new Array(24).fill(0),
                    backgroundColor: this.config.colors.primary,
                    borderRadius: 4,
                    maxBarThickness: 30
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return `Hour: ${context[0].label}`;
                            },
                            label: function(context) {
                                return `Tasks completed: ${context.parsed.y}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Tasks'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Hour of Day'
                        }
                    }
                },
                animation: {
                    duration: this.config.animationDuration,
                    easing: 'easeOutQuart'
                }
            }
        });

        // Load initial data
        this.loadTimeDistributionData();
    },

    /**
     * Add interactive enhancements to existing charts
     */
    addChartEnhancements(chart, type) {
        // Add drill-down functionality
        chart.options.onClick = (event, activeElements) => {
            if (activeElements.length > 0) {
                this.handleChartClick(chart, activeElements[0], type);
            }
        };

        // Add hover effects
        chart.options.onHover = (event, activeElements) => {
            event.native.target.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
        };

        // Update chart with enhanced animations
        if (chart.options.animation) {
            chart.options.animation.duration = this.config.animationDuration;
            chart.options.animation.easing = 'easeOutQuart';
        }

        chart.update();
    },

    /**
     * Handle chart click events for drill-down
     */
    handleChartClick(chart, element, type) {
        const dataIndex = element.index;
        const datasetIndex = element.datasetIndex;
        
        console.log(`Chart clicked: ${type}, Dataset: ${datasetIndex}, Index: ${dataIndex}`);
        
        // Show detailed view based on chart type
        switch(type) {
            case 'productivity':
                this.showProductivityDetails(dataIndex);
                break;
            case 'xp':
                this.showXPDetails(dataIndex);
                break;
            default:
                this.showGeneralDetails(type, dataIndex);
        }
    },

    /**
     * Setup real-time updates
     */
    setupRealTimeUpdates() {
        // Start update timer
        this.state.updateTimer = setInterval(() => {
            this.updateDashboard();
        }, this.config.updateInterval);

        // Add manual refresh button
        this.addRefreshButton();
        
        // Add last updated indicator
        this.addLastUpdatedIndicator();
    },

    /**
     * Update dashboard data
     */
    async updateDashboard() {
        if (this.state.isUpdating) return;
        
        this.state.isUpdating = true;
        this.showUpdatingIndicator();

        try {
            const data = await this.fetchLatestData();
            this.updateCharts(data);
            this.updateInsights(data);
            this.state.lastUpdate = new Date();
            this.updateLastUpdatedIndicator();
        } catch (error) {
            console.error('Failed to update dashboard:', error);
        } finally {
            this.state.isUpdating = false;
            this.hideUpdatingIndicator();
        }
    },

    /**
     * Fetch latest statistics data
     */
    async fetchLatestData() {
        const response = await fetch('/api/stats/latest/', {
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    },

    /**
     * Load task completion data
     */
    async loadTaskCompletionData(period = 7) {
        try {
            const response = await fetch(`/api/stats/task-completion/?period=${period}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (this.config.charts.taskCompletion) {
                this.config.charts.taskCompletion.data.datasets[0].data = [
                    data.completed || 0,
                    data.pending || 0,
                    data.overdue || 0
                ];
                this.config.charts.taskCompletion.update();
                
                // Update legend values
                const completedEl = document.getElementById('completed-count');
                const pendingEl = document.getElementById('pending-count');
                const overdueEl = document.getElementById('overdue-count');
                
                if (completedEl) completedEl.textContent = data.completed || 0;
                if (pendingEl) pendingEl.textContent = data.pending || 0;
                if (overdueEl) overdueEl.textContent = data.overdue || 0;
            }
        } catch (error) {
            console.error('Failed to load task completion data:', error);
            // Show placeholder data
            if (this.config.charts.taskCompletion) {
                this.config.charts.taskCompletion.data.datasets[0].data = [0, 0, 0];
                this.config.charts.taskCompletion.update();
            }
        }
    },

    /**
     * Load weekly activity data
     */
    async loadWeeklyActivityData() {
        try {
            const response = await fetch('/api/stats/weekly-activity/');
            const data = await response.json();
            
            if (this.config.charts.weeklyActivity && data.weekly_data) {
                this.config.charts.weeklyActivity.data.datasets[0].data = data.weekly_data;
                this.config.charts.weeklyActivity.update();
            }
        } catch (error) {
            console.error('Failed to load weekly activity data:', error);
        }
    },

    /**
     * Load time distribution data
     */
    async loadTimeDistributionData() {
        try {
            const response = await fetch('/api/stats/time-distribution/');
            const data = await response.json();
            
            if (this.config.charts.timeDistribution && data.hourly_data) {
                this.config.charts.timeDistribution.data.datasets[0].data = data.hourly_data;
                this.config.charts.timeDistribution.update();
                
                // Update insights
                if (data.insights) {
                    document.getElementById('peak-hour').textContent = data.insights.peak_hour || '--';
                    document.getElementById('avg-tasks').textContent = data.insights.avg_tasks || '--';
                    document.getElementById('most-productive').textContent = data.insights.most_productive || '--';
                    document.getElementById('completion-rate').textContent = (data.insights.completion_rate || 0) + '%';
                }
            }
        } catch (error) {
            console.error('Failed to load time distribution data:', error);
        }
    },

    /**
     * Setup interactive elements
     */
    setupInteractiveElements() {
        // Add chart controls
        this.addChartControls();
        
        // Add export buttons
        this.addExportButtons();
        
        // Add chart fullscreen functionality
        this.addFullscreenFeature();
    },

    /**
     * Utility functions
     */
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    },

    showUpdatingIndicator() {
        // Implementation for showing update indicator
    },

    hideUpdatingIndicator() {
        // Implementation for hiding update indicator
    },

    addRefreshButton() {
        // Implementation for adding refresh button
    },

    addLastUpdatedIndicator() {
        // Implementation for last updated indicator
    },

    updateLastUpdatedIndicator() {
        // Implementation for updating last updated time
    },

    // Placeholder methods for future implementation
    setupKeyboardShortcuts() {},
    setupExportFeatures() {},
    addInsightCards() {},
    addChartControls() {},
    addExportButtons() {},
    addFullscreenFeature() {},
    updateCharts(data) {},
    updateInsights(data) {},
    showProductivityDetails(index) {},
    showXPDetails(index) {},
    showGeneralDetails(type, index) {},
    refreshTimeDistribution() {
        this.loadTimeDistributionData();
    }
};

// Auto-initialize when DOM is ready (only on relevant pages)
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on pages that need advanced analytics
    const isStatsPage = window.location.pathname.includes('/dashboard/') || 
                       window.location.pathname.includes('/stats/') ||
                       document.querySelector('.card-header:contains("Statistics")') ||
                       document.querySelector('[data-stats-page]');
    
    if (isStatsPage) {
        // Initialize with a delay to ensure Chart.js is loaded
        setTimeout(() => {
            StatsEnhancements.init();
        }, 1000);
    }
});
