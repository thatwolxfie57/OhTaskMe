/**
 * AJAX Utilities Module
 * Provides smooth AJAX interactions without page reloads
 */

class AjaxManager {
    constructor() {
        this.csrfToken = this.getCsrfToken();
        this.loadingIndicators = new Map();
        this.init();
    }
    
    init() {
        // Handle AJAX form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.hasAttribute('data-ajax')) {
                e.preventDefault();
                this.handleFormSubmission(e.target);
            }
        });
        
        // Handle AJAX button clicks
        document.addEventListener('click', (e) => {
            if (e.target.hasAttribute('data-ajax-action')) {
                e.preventDefault();
                this.handleButtonAction(e.target);
            }
        });
        
        // Handle task completion toggles
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('task-complete-checkbox')) {
                this.updateTaskStatus(e.target);
            }
        });
    }
    
    getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    async handleFormSubmission(form) {
        const formData = new FormData(form);
        const url = form.action || window.location.href;
        const method = form.method || 'POST';
        
        try {
            this.showLoading(form);
            
            const response = await fetch(url, {
                method: method,
                body: formData,
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.handleSuccess(form, data);
            } else {
                this.handleError(form, data);
            }
            
        } catch (error) {
            this.handleError(form, { error: 'Network error occurred' });
        } finally {
            this.hideLoading(form);
        }
    }
    
    async handleButtonAction(button) {
        const action = button.dataset.ajaxAction;
        const url = button.dataset.url || button.href;
        const method = button.dataset.method || 'POST';
        const data = this.getButtonData(button);
        
        try {
            this.showLoading(button);
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: method !== 'GET' ? JSON.stringify(data) : null
            });
            
            const responseData = await response.json();
            
            if (response.ok) {
                this.handleButtonSuccess(button, responseData);
            } else {
                this.handleButtonError(button, responseData);
            }
            
        } catch (error) {
            this.handleButtonError(button, { error: 'Network error occurred' });
        } finally {
            this.hideLoading(button);
        }
    }
    
    async updateTaskStatus(checkbox) {
        const taskId = checkbox.dataset.taskId;
        const isCompleted = checkbox.checked;
        const taskRow = document.getElementById(`task-${taskId}`);
        
        try {
            // Optimistic UI update
            this.updateTaskRowAppearance(taskRow, isCompleted);
            
            const response = await fetch(`/tasks/${taskId}/toggle/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ completed: isCompleted })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                // Revert optimistic update on error
                checkbox.checked = !isCompleted;
                this.updateTaskRowAppearance(taskRow, !isCompleted);
                this.showToast('Error updating task status', 'error');
            } else {
                this.showToast(data.message || 'Task updated successfully', 'success');
                // Update any statistics or counters
                this.updateTaskCounters();
            }
            
        } catch (error) {
            // Revert optimistic update on error
            checkbox.checked = !isCompleted;
            this.updateTaskRowAppearance(taskRow, !isCompleted);
            this.showToast('Network error occurred', 'error');
        }
    }
    
    updateTaskRowAppearance(taskRow, isCompleted) {
        if (isCompleted) {
            taskRow.classList.add('task-completed');
            taskRow.style.opacity = '0.6';
        } else {
            taskRow.classList.remove('task-completed');
            taskRow.style.opacity = '1';
        }
    }
    
    updateTaskCounters() {
        // Update task completion counters if they exist
        const completedCount = document.querySelectorAll('.task-complete-checkbox:checked').length;
        const totalCount = document.querySelectorAll('.task-complete-checkbox').length;
        
        const counterElement = document.getElementById('task-completion-counter');
        if (counterElement) {
            counterElement.textContent = `${completedCount}/${totalCount} completed`;
        }
        
        // Update progress bar if it exists
        const progressBar = document.getElementById('task-progress-bar');
        if (progressBar && totalCount > 0) {
            const percentage = (completedCount / totalCount) * 100;
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', percentage);
        }
    }
    
    getButtonData(button) {
        const data = {};
        
        // Get data attributes
        Object.keys(button.dataset).forEach(key => {
            if (key.startsWith('param')) {
                const paramName = key.replace('param', '').toLowerCase();
                data[paramName] = button.dataset[key];
            }
        });
        
        return data;
    }
    
    handleSuccess(form, data) {
        if (data.redirect) {
            window.location.href = data.redirect;
        } else if (data.reload) {
            window.location.reload();
        } else {
            this.showToast(data.message || 'Success!', 'success');
            if (data.reset_form) {
                form.reset();
            }
            if (data.close_modal) {
                const modal = bootstrap.Modal.getInstance(form.closest('.modal'));
                if (modal) modal.hide();
            }
        }
    }
    
    handleError(form, data) {
        if (data.errors) {
            this.displayFormErrors(form, data.errors);
        } else {
            this.showToast(data.error || 'An error occurred', 'error');
        }
    }
    
    handleButtonSuccess(button, data) {
        if (data.redirect) {
            window.location.href = data.redirect;
        } else if (data.reload) {
            window.location.reload();
        } else {
            this.showToast(data.message || 'Success!', 'success');
            
            // Handle specific button actions
            if (data.hide_element) {
                const element = document.getElementById(data.hide_element);
                if (element) element.style.display = 'none';
            }
            
            if (data.update_text) {
                button.textContent = data.update_text;
            }
            
            if (data.disable_button) {
                button.disabled = true;
            }
        }
    }
    
    handleButtonError(button, data) {
        this.showToast(data.error || 'An error occurred', 'error');
    }
    
    displayFormErrors(form, errors) {
        // Clear existing errors
        form.querySelectorAll('.is-invalid').forEach(field => {
            field.classList.remove('is-invalid');
        });
        form.querySelectorAll('.invalid-feedback').forEach(feedback => {
            feedback.remove();
        });
        
        // Display new errors
        Object.keys(errors).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                field.classList.add('is-invalid');
                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.textContent = errors[fieldName].join(', ');
                field.parentNode.appendChild(feedback);
            }
        });
    }
    
    showLoading(element) {
        const loadingId = 'loading-' + Date.now();
        
        if (element.tagName === 'FORM') {
            const submitButton = element.querySelector('[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
                this.loadingIndicators.set(loadingId, { element: submitButton, originalText: submitButton.textContent });
            }
        } else {
            element.disabled = true;
            const originalText = element.innerHTML;
            element.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
            this.loadingIndicators.set(loadingId, { element, originalText });
        }
        
        element.dataset.loadingId = loadingId;
    }
    
    hideLoading(element) {
        const loadingId = element.dataset.loadingId;
        if (loadingId && this.loadingIndicators.has(loadingId)) {
            const { element: loadingElement, originalText } = this.loadingIndicators.get(loadingId);
            loadingElement.disabled = false;
            loadingElement.innerHTML = originalText;
            this.loadingIndicators.delete(loadingId);
            delete element.dataset.loadingId;
        }
    }
    
    showToast(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast
        const toast = document.createElement('div');
        toast.className = `toast show align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'primary'} border-0`;
        toast.setAttribute('role', 'alert');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
        
        // Enable Bootstrap toast functionality
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
}

// Initialize AJAX manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new AjaxManager();
});

// Export for use in other modules
window.AjaxManager = AjaxManager;
