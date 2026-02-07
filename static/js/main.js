// Custom JavaScript for OhTaskMe application

// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Task completion toggle
    const taskCheckboxes = document.querySelectorAll('.task-complete-checkbox');
    if (taskCheckboxes) {
        taskCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const taskId = this.dataset.taskId;
                const taskRow = document.getElementById(`task-${taskId}`);
                
                // Optimistic UI update
                if (this.checked) {
                    taskRow.classList.add('task-completed');
                } else {
                    taskRow.classList.remove('task-completed');
                }
                
                // Send AJAX request to update task status
                updateTaskStatus(taskId, this.checked);
            });
        });
    }
    
    // Function to update task status via AJAX
    function updateTaskStatus(taskId, completed) {
        const formData = new FormData();
        formData.append('task_id', taskId);
        
        fetch('/tasks/ajax/toggle/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log('Task updated successfully:', data);
                // You could add a toast notification here
            } else {
                throw new Error(data.message);
            }
        })
        .catch(error => {
            console.error('Error updating task:', error);
            // Revert the UI change on error
            const checkbox = document.querySelector(`.task-complete-checkbox[data-task-id="${taskId}"]`);
            const taskRow = document.getElementById(`task-${taskId}`);
            
            if (checkbox) {
                checkbox.checked = !completed;
            }
            
            if (taskRow) {
                if (!completed) {
                    taskRow.classList.add('task-completed');
                } else {
                    taskRow.classList.remove('task-completed');
                }
            }
            
            // Show error message
            alert('Failed to update task. Please try again.');
        });
    }
    
    // Function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Event type toggle for form fields
    const eventTypeSelect = document.getElementById('event-type-select');
    if (eventTypeSelect) {
        const activeEventFields = document.getElementById('active-event-fields');
        
        eventTypeSelect.addEventListener('change', function() {
            if (this.value === 'active') {
                activeEventFields.classList.remove('d-none');
            } else {
                activeEventFields.classList.add('d-none');
            }
        });
    }
    
    // Date and time pickers initialization (if using a date picker library)
    const dateInputs = document.querySelectorAll('.datepicker');
    if (dateInputs.length > 0) {
        dateInputs.forEach(input => {
            // If using flatpickr
            flatpickr(input, {
                enableTime: input.classList.contains('with-time'),
                dateFormat: input.classList.contains('with-time') ? "Y-m-d H:i" : "Y-m-d"
            });
        });
    }
});
