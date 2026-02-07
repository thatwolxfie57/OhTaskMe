/**
 * Calendar Enhancements for OhTaskMe
 * Provides interactive calendar functionality including drag-and-drop,
 * quick task creation, and real-time updates
 */

const CalendarEnhancements = {
    // Configuration
    config: {
        selectors: {
            calendar: '.calendar-table',
            calendarDay: '.calendar-day',
            taskItem: '.task-item',
            quickAddModal: '#quickAddModal',
            taskPreview: '#taskPreview'
        },
        classes: {
            dragOver: 'drag-over',
            dragging: 'dragging',
            selected: 'selected',
            highlighted: 'highlighted'
        },
        animations: {
            duration: 300,
            easing: 'ease-in-out'
        }
    },

    // State management
    state: {
        draggedTask: null,
        selectedDate: null,
        quickAddDate: null,
        isInitialized: false
    },

    /**
     * Initialize calendar enhancements
     */
    init() {
        if (this.state.isInitialized) return;
        
        console.log('Initializing Calendar Enhancements...');
        
        this.setupDragAndDrop();
        this.setupQuickActions();
        this.setupKeyboardShortcuts();
        this.setupDateSelection();
        this.setupTaskPreview();
        this.setupRealTimeUpdates();
        
        this.state.isInitialized = true;
        console.log('Calendar Enhancements initialized successfully');
    },

    /**
     * Setup drag and drop functionality for task rescheduling
     */
    setupDragAndDrop() {
        const calendar = document.querySelector(this.config.selectors.calendar);
        if (!calendar) return;

        // Make task items draggable
        this.makeTakssDraggable();

        // Setup drop zones on calendar days
        document.querySelectorAll(this.config.selectors.calendarDay).forEach(day => {
            this.setupDropZone(day);
        });
    },

    /**
     * Make task items draggable
     */
    makeTakssDraggable() {
        document.querySelectorAll(this.config.selectors.taskItem).forEach(taskItem => {
            taskItem.draggable = true;
            taskItem.style.cursor = 'move';

            taskItem.addEventListener('dragstart', (e) => {
                this.state.draggedTask = taskItem;
                taskItem.classList.add(this.config.classes.dragging);
                
                // Store task data
                const taskId = this.extractTaskId(taskItem);
                e.dataTransfer.setData('text/plain', taskId);
                e.dataTransfer.effectAllowed = 'move';
                
                // Visual feedback
                taskItem.style.opacity = '0.5';
            });

            taskItem.addEventListener('dragend', () => {
                taskItem.classList.remove(this.config.classes.dragging);
                taskItem.style.opacity = '1';
                this.state.draggedTask = null;
                
                // Remove all drag-over effects
                document.querySelectorAll('.' + this.config.classes.dragOver).forEach(el => {
                    el.classList.remove(this.config.classes.dragOver);
                });
            });
        });
    },

    /**
     * Setup drop zone for a calendar day
     */
    setupDropZone(dayElement) {
        dayElement.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            dayElement.classList.add(this.config.classes.dragOver);
        });

        dayElement.addEventListener('dragleave', (e) => {
            // Only remove if actually leaving the element
            if (!dayElement.contains(e.relatedTarget)) {
                dayElement.classList.remove(this.config.classes.dragOver);
            }
        });

        dayElement.addEventListener('drop', (e) => {
            e.preventDefault();
            dayElement.classList.remove(this.config.classes.dragOver);
            
            const taskId = e.dataTransfer.getData('text/plain');
            const targetDate = this.extractDateFromDay(dayElement);
            
            if (taskId && targetDate) {
                this.moveTask(taskId, targetDate);
            }
        });
    },

    /**
     * Setup quick actions (double-click to add task, right-click context menu)
     */
    setupQuickActions() {
        document.querySelectorAll(this.config.selectors.calendarDay).forEach(day => {
            // Double-click to create quick task
            day.addEventListener('dblclick', (e) => {
                e.preventDefault();
                const date = this.extractDateFromDay(day);
                if (date) {
                    this.openQuickTaskModal(date);
                }
            });

            // Right-click context menu
            day.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                const date = this.extractDateFromDay(day);
                if (date) {
                    this.showContextMenu(e.clientX, e.clientY, date);
                }
            });
        });

        // Close context menu on click elsewhere
        document.addEventListener('click', () => {
            this.hideContextMenu();
        });
    },

    /**
     * Setup keyboard shortcuts for calendar navigation
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Only process if not in input field
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.navigateMonth(-1);
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.navigateMonth(1);
                    break;
                case 't':
                case 'T':
                    e.preventDefault();
                    this.goToToday();
                    break;
                case 'n':
                case 'N':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        this.openQuickTaskModal();
                    }
                    break;
                case 'Escape':
                    this.hideContextMenu();
                    this.hideTaskPreview();
                    break;
            }
        });
    },

    /**
     * Setup date selection for highlighting
     */
    setupDateSelection() {
        document.querySelectorAll(this.config.selectors.calendarDay).forEach(day => {
            day.addEventListener('click', (e) => {
                // Don't select if clicking on a task
                if (e.target.closest(this.config.selectors.taskItem)) return;

                // Remove previous selection
                document.querySelectorAll('.' + this.config.classes.selected).forEach(el => {
                    el.classList.remove(this.config.classes.selected);
                });

                // Select current day
                day.classList.add(this.config.classes.selected);
                this.state.selectedDate = this.extractDateFromDay(day);
            });
        });
    },

    /**
     * Setup task preview on hover
     */
    setupTaskPreview() {
        document.querySelectorAll(this.config.selectors.taskItem).forEach(taskItem => {
            taskItem.addEventListener('mouseenter', (e) => {
                const taskData = this.extractTaskData(taskItem);
                if (taskData) {
                    this.showTaskPreview(e.clientX, e.clientY, taskData);
                }
            });

            taskItem.addEventListener('mouseleave', () => {
                this.hideTaskPreview();
            });
        });
    },

    /**
     * Setup real-time updates using Server-Sent Events or WebSocket
     */
    setupRealTimeUpdates() {
        // Only setup real-time updates if user is authenticated
        // Check for authentication indicators in the page
        const isAuthenticated = document.querySelector('a[href*="/logout/"]') || 
                               document.querySelector('.navbar-nav .dropdown') ||
                               document.body.classList.contains('authenticated');
        
        if (!isAuthenticated) {
            console.log('User not authenticated, skipping real-time updates');
            return;
        }

        // Check if server supports real-time updates
        if (typeof EventSource !== 'undefined') {
            try {
                const eventSource = new EventSource('/api/task-updates/');
                
                eventSource.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    this.handleRealTimeUpdate(data);
                };

                eventSource.onerror = (error) => {
                    console.log('Real-time updates connection error:', error);
                    eventSource.close();
                    // Fallback to periodic updates
                    this.setupPeriodicUpdates();
                };
            } catch (error) {
                console.log('Real-time updates not supported:', error);
                this.setupPeriodicUpdates();
            }
        } else {
            this.setupPeriodicUpdates();
        }
    },

    /**
     * Setup periodic updates as fallback
     */
    setupPeriodicUpdates() {
        // Only setup periodic updates if user is authenticated
        const isAuthenticated = document.querySelector('a[href*="/logout/"]') || 
                               document.querySelector('.navbar-nav .dropdown') ||
                               document.body.classList.contains('authenticated');
        
        if (!isAuthenticated) {
            return;
        }

        setInterval(() => {
            this.refreshCalendarView();
        }, 60000); // Refresh every minute
    },

    /**
     * Move task to new date
     */
    async moveTask(taskId, newDate) {
        if (!taskId || !newDate) return;

        try {
            // Show loading state
            this.showLoadingState();

            const response = await fetch('/api/move-task/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    task_id: taskId,
                    new_date: newDate
                })
            });

            if (response.status === 401) {
                // Handle authentication error
                this.showErrorMessage('Please log in to move tasks.');
                window.location.href = '/login/';
                return;
            }

            const result = await response.json();

            if (response.ok && result.success) {
                this.showSuccessMessage(`Task moved to ${newDate}`);
                
                // Refresh calendar view
                this.refreshCalendarView();
            } else {
                throw new Error(result.error || 'Failed to move task');
            }
        } catch (error) {
            console.error('Error moving task:', error);
            if (error.message.includes('401') || error.message.includes('Unauthorized')) {
                this.showErrorMessage('Please log in to move tasks.');
                window.location.href = '/login/';
            } else {
                this.showErrorMessage('Failed to move task. Please try again.');
            }
            
            // Revert the visual change if it was made
            this.refreshCalendarView();
        } finally {
            this.hideLoadingState();
        }
    },

    /**
     * Open quick task creation modal
     */
    openQuickTaskModal(date = null) {
        this.state.quickAddDate = date || this.getTodayDate();
        
        // Create modal if it doesn't exist
        if (!document.querySelector(this.config.selectors.quickAddModal)) {
            this.createQuickAddModal();
        }

        // Set date in modal
        const dateInput = document.querySelector(this.config.selectors.quickAddModal + ' #quickDate');
        if (dateInput) {
            dateInput.value = this.state.quickAddDate;
        }

        // Show modal
        const modal = new bootstrap.Modal(document.querySelector(this.config.selectors.quickAddModal));
        modal.show();
    },

    /**
     * Create quick add modal HTML
     */
    createQuickAddModal() {
        const modalHTML = `
            <div class="modal fade" id="quickAddModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Quick Add Task</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="quickAddForm">
                                <div class="mb-3">
                                    <label for="quickDescription" class="form-label">Description</label>
                                    <input type="text" class="form-control" id="quickDescription" 
                                           placeholder="Enter task description..." required>
                                </div>
                                <div class="row">
                                    <div class="col-md-6">
                                        <label for="quickDate" class="form-label">Date</label>
                                        <input type="date" class="form-control" id="quickDate" required>
                                    </div>
                                    <div class="col-md-6">
                                        <label for="quickTime" class="form-label">Time</label>
                                        <input type="time" class="form-control" id="quickTime" required>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" onclick="CalendarEnhancements.createQuickTask()">Create Task</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    },

    /**
     * Create quick task
     */
    async createQuickTask() {
        const form = document.getElementById('quickAddForm');
        const description = document.getElementById('quickDescription').value;
        const date = document.getElementById('quickDate').value;
        const time = document.getElementById('quickTime').value;

        if (!description || !date || !time) {
            this.showErrorMessage('Please fill in all fields');
            return;
        }

        try {
            const response = await fetch('/api/quick-create-task/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    description,
                    scheduled_time: `${date}T${time}`
                })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.showSuccessMessage('Task created successfully');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.querySelector(this.config.selectors.quickAddModal));
                if (modal) {
                    modal.hide();
                }
                
                // Clear form
                form.reset();
                
                // Refresh calendar
                this.refreshCalendarView();
            } else {
                throw new Error(result.error || 'Failed to create task');
            }
        } catch (error) {
            console.error('Error creating task:', error);
            this.showErrorMessage('Failed to create task. Please try again.');
        }
    },

    /**
     * Show context menu
     */
    showContextMenu(x, y, date) {
        // Remove existing context menu
        this.hideContextMenu();

        const menuHTML = `
            <div id="calendarContextMenu" class="context-menu" style="left: ${x}px; top: ${y}px;">
                <div class="context-menu-item" onclick="CalendarEnhancements.openQuickTaskModal('${date}')">
                    <i class="fas fa-plus me-2"></i>Add Task
                </div>
                <div class="context-menu-item" onclick="CalendarEnhancements.viewDayDetails('${date}')">
                    <i class="fas fa-eye me-2"></i>View Day
                </div>
                <div class="context-menu-divider"></div>
                <div class="context-menu-item" onclick="CalendarEnhancements.goToDate('${date}')">
                    <i class="fas fa-calendar me-2"></i>Go to Date
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', menuHTML);
    },

    /**
     * Hide context menu
     */
    hideContextMenu() {
        const menu = document.getElementById('calendarContextMenu');
        if (menu) {
            menu.remove();
        }
    },

    /**
     * Utility functions
     */
    extractTaskId(taskElement) {
        const link = taskElement.querySelector('a');
        if (link && link.href) {
            const matches = link.href.match(/\/tasks\/(\d+)\//);
            return matches ? matches[1] : null;
        }
        return null;
    },

    extractDateFromDay(dayElement) {
        const dayNumber = dayElement.querySelector('.day-number');
        if (!dayNumber) return null;

        // Extract from URL or data attribute
        const currentDate = new Date();
        const year = new URLSearchParams(window.location.search).get('year') || currentDate.getFullYear();
        const month = new URLSearchParams(window.location.search).get('month') || (currentDate.getMonth() + 1);
        const day = dayNumber.textContent.trim();

        return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    },

    extractTaskData(taskElement) {
        const link = taskElement.querySelector('a');
        const description = taskElement.textContent.trim();
        const tooltip = taskElement.getAttribute('title');
        
        return {
            id: this.extractTaskId(taskElement),
            description,
            tooltip,
            element: taskElement
        };
    },

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    },

    getTodayDate() {
        return new Date().toISOString().split('T')[0];
    },

    // Navigation functions
    navigateMonth(direction) {
        const currentUrl = new URL(window.location);
        const year = parseInt(currentUrl.searchParams.get('year')) || new Date().getFullYear();
        const month = parseInt(currentUrl.searchParams.get('month')) || new Date().getMonth() + 1;

        let newYear = year;
        let newMonth = month + direction;

        if (newMonth > 12) {
            newMonth = 1;
            newYear++;
        } else if (newMonth < 1) {
            newMonth = 12;
            newYear--;
        }

        currentUrl.searchParams.set('year', newYear);
        currentUrl.searchParams.set('month', newMonth);
        window.location.href = currentUrl.toString();
    },

    goToToday() {
        const today = new Date();
        const url = new URL(window.location);
        url.searchParams.delete('year');
        url.searchParams.delete('month');
        window.location.href = url.pathname;
    },

    // UI feedback functions
    showSuccessMessage(message) {
        if (typeof AJAXManager !== 'undefined' && AJAXManager.showToast) {
            AJAXManager.showToast(message, 'success');
        } else {
            alert(message);
        }
    },

    showErrorMessage(message) {
        if (typeof AJAXManager !== 'undefined' && AJAXManager.showToast) {
            AJAXManager.showToast(message, 'error');
        } else {
            alert(message);
        }
    },

    showLoadingState() {
        document.body.style.cursor = 'wait';
    },

    hideLoadingState() {
        document.body.style.cursor = 'default';
    },

    refreshCalendarView() {
        window.location.reload();
    },

    // Placeholder functions for future implementation
    showTaskPreview(x, y, taskData) {
        // Implementation for task preview tooltip
    },

    hideTaskPreview() {
        // Implementation for hiding task preview
    },

    handleRealTimeUpdate(data) {
        // Implementation for real-time updates
        console.log('Real-time update received:', data);
    },

    viewDayDetails(date) {
        // Implementation for day details view
        console.log('View day details:', date);
    },

    goToDate(date) {
        // Implementation for going to specific date
        console.log('Go to date:', date);
    }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    CalendarEnhancements.init();
});
