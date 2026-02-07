/**
 * Date and Time Picker Module
 * Provides enhanced date/time input functionality using Flatpickr
 */

class DateTimePicker {
    constructor() {
        this.defaultConfig = {
            enableTime: false,
            dateFormat: "Y-m-d",
            altInput: true,
            altFormat: "F j, Y",
            allowInput: true,
            clickOpens: true,
            locale: "default"
        };
        
        this.timeConfig = {
            enableTime: true,
            noCalendar: true,
            dateFormat: "H:i",
            altInput: true,
            altFormat: "h:i K",
            time_24hr: false
        };
        
        this.dateTimeConfig = {
            enableTime: true,
            dateFormat: "Y-m-d H:i",
            altInput: true,
            altFormat: "F j, Y at h:i K",
            time_24hr: false
        };
        
        this.init();
    }
    
    init() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializePickers());
        } else {
            this.initializePickers();
        }
        
        // Re-initialize pickers when new content is added dynamically
        document.addEventListener('picker:refresh', () => this.initializePickers());
    }
    
    initializePickers() {
        // Initialize date pickers
        this.initDatePickers();
        
        // Initialize time pickers
        this.initTimePickers();
        
        // Initialize datetime pickers
        this.initDateTimePickers();
        
        // Initialize special pickers
        this.initSpecialPickers();
    }
    
    initDatePickers() {
        const datePickers = document.querySelectorAll('.date-picker, input[type="date"]:not(.no-picker)');
        
        datePickers.forEach(picker => {
            if (picker._flatpickr) return; // Already initialized
            
            const config = { ...this.defaultConfig };
            
            // Custom configurations based on data attributes
            if (picker.dataset.minDate) {
                config.minDate = picker.dataset.minDate === 'today' ? 'today' : picker.dataset.minDate;
            }
            
            if (picker.dataset.maxDate) {
                config.maxDate = picker.dataset.maxDate;
            }
            
            if (picker.dataset.disable) {
                config.disable = JSON.parse(picker.dataset.disable);
            }
            
            if (picker.dataset.enable) {
                config.enable = JSON.parse(picker.dataset.enable);
            }
            
            // Task scheduling specific config
            if (picker.classList.contains('task-date-picker')) {
                config.minDate = 'today';
                config.onChange = (selectedDates, dateStr, instance) => {
                    this.updateTaskPreview(picker, selectedDates[0]);
                };
            }
            
            // Event date specific config
            if (picker.classList.contains('event-date-picker')) {
                config.minDate = 'today';
                config.onChange = (selectedDates, dateStr, instance) => {
                    this.updateEventPreview(picker, selectedDates[0]);
                };
            }
            
            flatpickr(picker, config);
        });
    }
    
    initTimePickers() {
        const timePickers = document.querySelectorAll('.time-picker, input[type="time"]:not(.no-picker)');
        
        timePickers.forEach(picker => {
            if (picker._flatpickr) return; // Already initialized
            
            const config = { ...this.timeConfig };
            
            // 24-hour format option
            if (picker.dataset.format24) {
                config.time_24hr = true;
                config.altFormat = "H:i";
            }
            
            // Default time
            if (picker.dataset.defaultTime) {
                config.defaultDate = picker.dataset.defaultTime;
            }
            
            flatpickr(picker, config);
        });
    }
    
    initDateTimePickers() {
        const dateTimePickers = document.querySelectorAll('.datetime-picker, input[type="datetime-local"]:not(.no-picker)');
        
        dateTimePickers.forEach(picker => {
            if (picker._flatpickr) return; // Already initialized
            
            const config = { ...this.dateTimeConfig };
            
            // Custom configurations
            if (picker.dataset.minDate) {
                config.minDate = picker.dataset.minDate === 'today' ? 'today' : picker.dataset.minDate;
            }
            
            if (picker.dataset.maxDate) {
                config.maxDate = picker.dataset.maxDate;
            }
            
            // 24-hour format option
            if (picker.dataset.format24) {
                config.time_24hr = true;
                config.altFormat = "F j, Y at H:i";
            }
            
            // Event specific config
            if (picker.classList.contains('event-datetime-picker')) {
                config.minDate = 'today';
                config.onChange = (selectedDates, dateStr, instance) => {
                    this.updateEventDateTime(picker, selectedDates[0]);
                };
            }
            
            flatpickr(picker, config);
        });
    }
    
    initSpecialPickers() {
        // Preparation start date picker (must be before event date)
        const prepDatePickers = document.querySelectorAll('.prep-date-picker');
        prepDatePickers.forEach(picker => {
            if (picker._flatpickr) return;
            
            const eventDateField = document.getElementById('id_event_time');
            const config = {
                ...this.defaultConfig,
                maxDate: 'today',
                onChange: (selectedDates, dateStr, instance) => {
                    this.updatePreparationPreview(picker, selectedDates[0]);
                }
            };
            
            // Set max date based on event date
            if (eventDateField && eventDateField.value) {
                config.maxDate = new Date(eventDateField.value);
            }
            
            flatpickr(picker, config);
            
            // Update max date when event date changes
            if (eventDateField) {
                eventDateField.addEventListener('change', () => {
                    if (eventDateField.value) {
                        picker._flatpickr.set('maxDate', new Date(eventDateField.value));
                    }
                });
            }
        });
        
        // Date range pickers
        const rangePickers = document.querySelectorAll('.date-range-picker');
        rangePickers.forEach(picker => {
            if (picker._flatpickr) return;
            
            const config = {
                ...this.defaultConfig,
                mode: "range",
                dateFormat: "Y-m-d",
                altFormat: "F j, Y",
                onChange: (selectedDates, dateStr, instance) => {
                    this.updateDateRange(picker, selectedDates);
                }
            };
            
            flatpickr(picker, config);
        });
    }
    
    updateTaskPreview(picker, selectedDate) {
        const previewElement = document.getElementById('task-date-preview');
        if (previewElement && selectedDate) {
            const formattedDate = selectedDate.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            previewElement.textContent = `Scheduled for ${formattedDate}`;
            previewElement.style.display = 'block';
            
            // Check for existing tasks on this date
            this.checkTaskConflicts(selectedDate);
        }
    }
    
    updateEventPreview(picker, selectedDate) {
        const previewElement = document.getElementById('event-date-preview');
        if (previewElement && selectedDate) {
            const formattedDate = selectedDate.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            previewElement.textContent = `Event scheduled for ${formattedDate}`;
            previewElement.style.display = 'block';
            
            // Update preparation date picker constraints
            const prepPickers = document.querySelectorAll('.prep-date-picker');
            prepPickers.forEach(prepPicker => {
                if (prepPicker._flatpickr) {
                    prepPicker._flatpickr.set('maxDate', selectedDate);
                }
            });
        }
    }
    
    updateEventDateTime(picker, selectedDateTime) {
        if (selectedDateTime) {
            // Trigger event preview update
            this.updateEventPreview(picker, selectedDateTime);
            
            // Check for scheduling conflicts
            this.checkEventConflicts(selectedDateTime);
            
            // Suggest preparation tasks if this is an active event
            if (picker.closest('form').querySelector('#id_event_type').value === 'active') {
                this.suggestPreparationTasks(selectedDateTime);
            }
        }
    }
    
    updatePreparationPreview(picker, selectedDate) {
        const eventDateField = document.getElementById('id_event_time');
        if (eventDateField && eventDateField.value && selectedDate) {
            const eventDate = new Date(eventDateField.value);
            const diffTime = Math.abs(eventDate - selectedDate);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            const previewElement = document.getElementById('prep-duration-preview');
            if (previewElement) {
                previewElement.textContent = `${diffDays} days of preparation time`;
                previewElement.style.display = 'block';
            }
            
            // Generate task preview
            this.generateTaskPreview(diffDays);
        }
    }
    
    updateDateRange(picker, selectedDates) {
        if (selectedDates.length === 2) {
            const startDate = selectedDates[0];
            const endDate = selectedDates[1];
            const diffTime = Math.abs(endDate - startDate);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
            
            const previewElement = document.getElementById('date-range-preview');
            if (previewElement) {
                previewElement.textContent = `${diffDays} days selected`;
                previewElement.style.display = 'block';
            }
        }
    }
    
    async checkTaskConflicts(date) {
        try {
            const response = await fetch(`/api/conflicts/?start_time=${date.toISOString()}&end_time=${new Date(date.getTime() + 3600000).toISOString()}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            if (response.ok) {
                const data = await response.json();
                const conflictElement = document.getElementById('task-conflicts');
                
                if (data.conflicts && data.conflicts.length > 0) {
                    conflictElement.innerHTML = `
                        <div class="alert alert-warning">
                            <strong>Potential conflicts found:</strong>
                            <ul class="mb-0 mt-2">
                                ${data.conflicts.map(conflict => `<li>${conflict.title} (${conflict.type})</li>`).join('')}
                            </ul>
                        </div>
                    `;
                    conflictElement.style.display = 'block';
                } else {
                    conflictElement.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error checking task conflicts:', error);
        }
    }
    
    async checkEventConflicts(dateTime) {
        try {
            const endTime = new Date(dateTime.getTime() + 3600000); // Add 1 hour
            const response = await fetch(`/api/conflicts/?start_time=${dateTime.toISOString()}&end_time=${endTime.toISOString()}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            if (response.ok) {
                const data = await response.json();
                const conflictElement = document.getElementById('event-conflicts');
                
                if (data.conflicts && data.conflicts.length > 0) {
                    conflictElement.innerHTML = `
                        <div class="alert alert-warning">
                            <strong>Potential conflicts found:</strong>
                            <ul class="mb-0 mt-2">
                                ${data.conflicts.map(conflict => `<li>${conflict.title} (${conflict.type})</li>`).join('')}
                            </ul>
                        </div>
                    `;
                    conflictElement.style.display = 'block';
                } else {
                    conflictElement.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error checking event conflicts:', error);
        }
    }
    
    generateTaskPreview(preparationDays) {
        const previewElement = document.getElementById('generated-tasks-preview');
        if (previewElement) {
            // This would integrate with the AI task generation system
            previewElement.innerHTML = `
                <div class="card">
                    <div class="card-header">
                        <h6>Suggested Preparation Tasks</h6>
                    </div>
                    <div class="card-body">
                        <div class="spinner-border spinner-border-sm me-2"></div>
                        Generating personalized tasks...
                    </div>
                </div>
            `;
            previewElement.style.display = 'block';
            
            // Simulate task generation (would be replaced with actual API call)
            setTimeout(() => {
                this.displayGeneratedTasks(preparationDays);
            }, 2000);
        }
    }
    
    displayGeneratedTasks(preparationDays) {
        const previewElement = document.getElementById('generated-tasks-preview');
        if (previewElement) {
            const sampleTasks = [
                'Review event agenda and requirements',
                'Prepare necessary materials and documents',
                'Confirm logistics and transportation',
                'Final preparation and review'
            ];
            
            previewElement.innerHTML = `
                <div class="card">
                    <div class="card-header">
                        <h6>Suggested Preparation Tasks (${preparationDays} days)</h6>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            ${sampleTasks.map((task, index) => `
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    ${task}
                                    <small class="text-muted">Day ${index + 1}</small>
                                </li>
                            `).join('')}
                        </ul>
                        <div class="mt-3">
                            <button type="button" class="btn btn-sm btn-success" onclick="acceptGeneratedTasks()">
                                Accept Tasks
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-secondary" onclick="regenerateTasks()">
                                Regenerate
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    // Utility method to refresh all pickers
    refresh() {
        document.dispatchEvent(new CustomEvent('picker:refresh'));
    }
    
    // Utility method to destroy all pickers
    destroy() {
        const allPickers = document.querySelectorAll('.flatpickr-input');
        allPickers.forEach(picker => {
            if (picker._flatpickr) {
                picker._flatpickr.destroy();
            }
        });
    }
}

// Global functions for task management
window.acceptGeneratedTasks = function() {
    // Implementation for accepting generated tasks
    console.log('Accepting generated tasks...');
    // This would integrate with the task creation API
};

window.regenerateTasks = function() {
    // Implementation for regenerating tasks
    console.log('Regenerating tasks...');
    // This would call the AI task generation API again
};

// Initialize date/time pickers when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if Flatpickr is available
    if (typeof flatpickr !== 'undefined') {
        new DateTimePicker();
    } else {
        console.warn('Flatpickr library not found. Date/time pickers will not be enhanced.');
    }
});

// Export for use in other modules
window.DateTimePicker = DateTimePicker;
