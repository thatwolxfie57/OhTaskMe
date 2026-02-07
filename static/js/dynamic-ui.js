/**
 * Dynamic UI Module
 * Handles dynamic user interface interactions for events and tasks
 */

class DynamicUI {
    constructor() {
        this.activeEventFields = [
            'total_work_hours',
            'daily_task_time',
            'preparation_start_date'
        ];
        
        this.init();
    }
    
    init() {
        // Initialize event type toggles
        this.initEventTypeToggles();
        
        // Initialize task preview functionality
        this.initTaskPreview();
        
        // Initialize dynamic form fields
        this.initDynamicFields();
        
        // Initialize collapsible sections
        this.initCollapsibleSections();
        
        // Initialize live form updates
        this.initLiveFormUpdates();
    }
    
    initEventTypeToggles() {
        // Handle event type radio buttons
        const eventTypeRadios = document.querySelectorAll('input[name="event_type"]');
        eventTypeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.toggleEventTypeFields(e.target.value);
            });
        });
        
        // Initialize on page load
        const selectedType = document.querySelector('input[name="event_type"]:checked');
        if (selectedType) {
            this.toggleEventTypeFields(selectedType.value);
        }
        
        // Handle event type select dropdown
        const eventTypeSelect = document.getElementById('id_event_type');
        if (eventTypeSelect) {
            eventTypeSelect.addEventListener('change', (e) => {
                this.toggleEventTypeFields(e.target.value);
            });
            
            // Initialize on page load
            this.toggleEventTypeFields(eventTypeSelect.value);
        }
    }
    
    toggleEventTypeFields(eventType) {
        const preparationSection = document.getElementById('preparation-fields');
        const taskPreviewSection = document.getElementById('task-preview-section');
        
        if (eventType === 'active') {
            // Show active event fields
            if (preparationSection) {
                preparationSection.style.display = 'block';
                this.animateSlideDown(preparationSection);
            }
            
            if (taskPreviewSection) {
                taskPreviewSection.style.display = 'block';
                this.animateSlideDown(taskPreviewSection);
            }
            
            // Make preparation fields required
            this.activeEventFields.forEach(fieldName => {
                const field = document.getElementById(`id_${fieldName}`);
                if (field) {
                    field.required = true;
                    field.closest('.form-group')?.classList.add('required');
                }
            });
            
            // Show help text for active events
            this.showActiveEventHelp();
            
        } else {
            // Hide active event fields
            if (preparationSection) {
                this.animateSlideUp(preparationSection);
            }
            
            if (taskPreviewSection) {
                this.animateSlideUp(taskPreviewSection);
            }
            
            // Remove required attribute from preparation fields
            this.activeEventFields.forEach(fieldName => {
                const field = document.getElementById(`id_${fieldName}`);
                if (field) {
                    field.required = false;
                    field.closest('.form-group')?.classList.remove('required');
                }
            });
            
            // Hide help text
            this.hideActiveEventHelp();
        }
    }
    
    initTaskPreview() {
        // Listen for changes in preparation fields
        const workHoursField = document.getElementById('id_total_work_hours');
        const dailyTimeField = document.getElementById('id_daily_task_time');
        const startDateField = document.getElementById('id_preparation_start_date');
        const eventDateField = document.getElementById('id_event_time');
        
        [workHoursField, dailyTimeField, startDateField, eventDateField].forEach(field => {
            if (field) {
                field.addEventListener('input', () => this.updateTaskPreview());
                field.addEventListener('change', () => this.updateTaskPreview());
            }
        });
        
        // Preview button
        const previewButton = document.getElementById('preview-tasks-btn');
        if (previewButton) {
            previewButton.addEventListener('click', () => this.generateTaskPreview());
        }
    }
    
    updateTaskPreview() {
        const workHours = document.getElementById('id_total_work_hours')?.value;
        const dailyTime = document.getElementById('id_daily_task_time')?.value;
        const startDate = document.getElementById('id_preparation_start_date')?.value;
        const eventDate = document.getElementById('id_event_time')?.value;
        
        if (workHours && dailyTime && startDate && eventDate) {
            this.calculateTaskDistribution(workHours, dailyTime, startDate, eventDate);
        }
    }
    
    calculateTaskDistribution(totalHours, dailyHours, startDate, eventDate) {
        const start = new Date(startDate);
        const event = new Date(eventDate);
        const diffTime = Math.abs(event - start);
        const availableDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        const dailyHoursFloat = parseFloat(dailyHours);
        const totalHoursFloat = parseFloat(totalHours);
        
        const recommendedDays = Math.ceil(totalHoursFloat / dailyHoursFloat);
        
        const previewElement = document.getElementById('task-distribution-preview');
        if (previewElement) {
            let html = `
                <div class="card">
                    <div class="card-header">
                        <h6><i class="fas fa-calculator me-2"></i>Task Distribution Preview</h6>
                    </div>
                    <div class="card-body">
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <strong>Total Work Required:</strong> ${totalHours} hours
                            </div>
                            <div class="col-md-6">
                                <strong>Daily Work Time:</strong> ${dailyHours} hours
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <strong>Available Days:</strong> ${availableDays} days
                            </div>
                            <div class="col-md-6">
                                <strong>Recommended Days:</strong> ${recommendedDays} days
                            </div>
                        </div>
            `;
            
            if (recommendedDays > availableDays) {
                html += `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <strong>Warning:</strong> You may need to work ${(totalHoursFloat / availableDays).toFixed(1)} hours per day to complete all tasks on time.
                    </div>
                `;
            } else {
                html += `
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle me-2"></i>
                        <strong>Good:</strong> You have sufficient time for preparation with the planned schedule.
                    </div>
                `;
            }
            
            html += `
                        <div class="mt-3">
                            <button type="button" class="btn btn-sm btn-primary" onclick="generateDetailedPreview()">
                                <i class="fas fa-eye me-2"></i>Generate Detailed Preview
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            previewElement.innerHTML = html;
            previewElement.style.display = 'block';
        }
    }
    
    generateTaskPreview() {
        const previewContainer = document.getElementById('generated-tasks-container');
        if (!previewContainer) return;
        
        // Show loading state
        previewContainer.innerHTML = `
            <div class="card">
                <div class="card-body text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Generating personalized preparation tasks...</p>
                </div>
            </div>
        `;
        
        // Simulate API call (replace with actual AI integration)
        setTimeout(() => {
            this.displayGeneratedTasks();
        }, 2000);
    }
    
    displayGeneratedTasks() {
        const previewContainer = document.getElementById('generated-tasks-container');
        if (!previewContainer) return;
        
        // Sample generated tasks (replace with actual AI-generated content)
        const sampleTasks = [
            {
                title: "Research event requirements and agenda",
                description: "Review all materials and understand expectations",
                estimatedTime: "2 hours",
                priority: "high",
                day: 1,
                confidence: 0.92
            },
            {
                title: "Prepare presentation materials",
                description: "Create slides and gather supporting documents",
                estimatedTime: "3 hours",
                priority: "high",
                day: 2,
                confidence: 0.88
            },
            {
                title: "Practice presentation and rehearse",
                description: "Run through presentation multiple times",
                estimatedTime: "2 hours",
                priority: "medium",
                day: 3,
                confidence: 0.85
            },
            {
                title: "Final preparation and material organization",
                description: "Organize all materials and do final checks",
                estimatedTime: "1 hour",
                priority: "medium",
                day: 4,
                confidence: 0.90
            }
        ];
        
        let html = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6><i class="fas fa-magic me-2"></i>AI-Generated Preparation Tasks</h6>
                    <span class="badge bg-primary">${sampleTasks.length} tasks</span>
                </div>
                <div class="card-body">
        `;
        
        sampleTasks.forEach((task, index) => {
            const confidenceColor = task.confidence >= 0.9 ? 'success' : 
                                   task.confidence >= 0.8 ? 'warning' : 'danger';
            
            html += `
                <div class="task-preview-item mb-3 p-3 border rounded" data-task-index="${index}">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div class="form-check">
                            <input class="form-check-input task-accept-checkbox" type="checkbox" 
                                   id="task-${index}" checked>
                            <label class="form-check-label fw-bold" for="task-${index}">
                                ${task.title}
                            </label>
                        </div>
                        <div class="d-flex gap-2">
                            <span class="badge bg-${task.priority === 'high' ? 'danger' : 'warning'}">${task.priority}</span>
                            <span class="badge bg-${confidenceColor}">
                                ${(task.confidence * 100).toFixed(0)}% confidence
                            </span>
                        </div>
                    </div>
                    <p class="text-muted mb-2">${task.description}</p>
                    <div class="row">
                        <div class="col-md-4">
                            <small><i class="fas fa-clock me-1"></i>Estimated: ${task.estimatedTime}</small>
                        </div>
                        <div class="col-md-4">
                            <small><i class="fas fa-calendar me-1"></i>Day ${task.day}</small>
                        </div>
                        <div class="col-md-4">
                            <button type="button" class="btn btn-sm btn-outline-primary" 
                                    onclick="editGeneratedTask(${index})">
                                <i class="fas fa-edit me-1"></i>Edit
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += `
                    <div class="mt-4 d-flex gap-2">
                        <button type="button" class="btn btn-success" onclick="acceptSelectedTasks()">
                            <i class="fas fa-check me-2"></i>Accept Selected Tasks
                        </button>
                        <button type="button" class="btn btn-outline-secondary" onclick="regenerateAllTasks()">
                            <i class="fas fa-sync me-2"></i>Regenerate All
                        </button>
                        <button type="button" class="btn btn-outline-info" onclick="addCustomTask()">
                            <i class="fas fa-plus me-2"></i>Add Custom Task
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        previewContainer.innerHTML = html;
    }
    
    initDynamicFields() {
        // Dynamic field visibility based on form values
        const conditionalFields = document.querySelectorAll('[data-show-when]');
        
        conditionalFields.forEach(field => {
            const condition = field.dataset.showWhen;
            const [targetField, expectedValue] = condition.split('=');
            
            const targetElement = document.getElementById(targetField) || 
                                document.querySelector(`[name="${targetField}"]`);
            
            if (targetElement) {
                targetElement.addEventListener('change', () => {
                    if (targetElement.value === expectedValue) {
                        this.animateSlideDown(field);
                    } else {
                        this.animateSlideUp(field);
                    }
                });
                
                // Initialize visibility
                if (targetElement.value === expectedValue) {
                    field.style.display = 'block';
                } else {
                    field.style.display = 'none';
                }
            }
        });
    }
    
    initCollapsibleSections() {
        const collapsibleTriggers = document.querySelectorAll('[data-bs-toggle="collapse"]');
        
        collapsibleTriggers.forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                const icon = trigger.querySelector('i');
                if (icon) {
                    setTimeout(() => {
                        const target = document.querySelector(trigger.dataset.bsTarget);
                        if (target.classList.contains('show')) {
                            icon.classList.remove('fa-chevron-down');
                            icon.classList.add('fa-chevron-up');
                        } else {
                            icon.classList.remove('fa-chevron-up');
                            icon.classList.add('fa-chevron-down');
                        }
                    }, 350); // Bootstrap collapse transition time
                }
            });
        });
    }
    
    initLiveFormUpdates() {
        // Live character counters
        const textFields = document.querySelectorAll('textarea[data-max-length], input[data-max-length]');
        
        textFields.forEach(field => {
            const maxLength = parseInt(field.dataset.maxLength);
            const counterId = field.id + '-counter';
            
            // Create counter element if it doesn't exist
            let counter = document.getElementById(counterId);
            if (!counter) {
                counter = document.createElement('small');
                counter.id = counterId;
                counter.className = 'text-muted form-text';
                field.parentNode.appendChild(counter);
            }
            
            const updateCounter = () => {
                const remaining = maxLength - field.value.length;
                counter.textContent = `${remaining} characters remaining`;
                
                if (remaining < 20) {
                    counter.className = 'text-warning form-text';
                } else if (remaining < 0) {
                    counter.className = 'text-danger form-text';
                } else {
                    counter.className = 'text-muted form-text';
                }
            };
            
            field.addEventListener('input', updateCounter);
            updateCounter(); // Initialize
        });
        
        // Live form validation feedback
        const requiredFields = document.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            field.addEventListener('blur', () => {
                if (field.value.trim() === '') {
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                    field.classList.add('is-valid');
                }
            });
        });
    }
    
    // Animation utilities
    animateSlideDown(element) {
        element.style.overflow = 'hidden';
        element.style.height = '0px';
        element.style.display = 'block';
        
        const height = element.scrollHeight + 'px';
        element.style.transition = 'height 0.3s ease-in-out';
        
        setTimeout(() => {
            element.style.height = height;
        }, 10);
        
        setTimeout(() => {
            element.style.height = '';
            element.style.overflow = '';
            element.style.transition = '';
        }, 300);
    }
    
    animateSlideUp(element) {
        element.style.overflow = 'hidden';
        element.style.height = element.scrollHeight + 'px';
        element.style.transition = 'height 0.3s ease-in-out';
        
        setTimeout(() => {
            element.style.height = '0px';
        }, 10);
        
        setTimeout(() => {
            element.style.display = 'none';
            element.style.height = '';
            element.style.overflow = '';
            element.style.transition = '';
        }, 300);
    }
    
    showActiveEventHelp() {
        const helpSection = document.getElementById('active-event-help');
        if (helpSection) {
            helpSection.style.display = 'block';
            this.animateSlideDown(helpSection);
        }
    }
    
    hideActiveEventHelp() {
        const helpSection = document.getElementById('active-event-help');
        if (helpSection) {
            this.animateSlideUp(helpSection);
        }
    }
}

// Global functions for task management
window.generateDetailedPreview = function() {
    const dynamicUI = window.dynamicUIInstance;
    if (dynamicUI) {
        dynamicUI.generateTaskPreview();
    }
};

window.editGeneratedTask = function(taskIndex) {
    // Implementation for editing a generated task
    console.log('Editing task:', taskIndex);
    // This would open a modal or inline editor
};

window.acceptSelectedTasks = function() {
    const selectedTasks = document.querySelectorAll('.task-accept-checkbox:checked');
    console.log('Accepting', selectedTasks.length, 'tasks');
    // This would integrate with the task creation API
};

window.regenerateAllTasks = function() {
    const dynamicUI = window.dynamicUIInstance;
    if (dynamicUI) {
        dynamicUI.generateTaskPreview();
    }
};

window.addCustomTask = function() {
    // Implementation for adding a custom task to the generated list
    console.log('Adding custom task');
    // This would open a form for custom task creation
};

// Initialize dynamic UI when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dynamicUIInstance = new DynamicUI();
});

// Export for use in other modules
window.DynamicUI = DynamicUI;
