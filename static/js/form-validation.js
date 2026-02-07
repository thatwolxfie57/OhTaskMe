/**
 * Form Validation Module
 * Provides client-side validation for all forms in the application
 */

class FormValidator {
    constructor() {
        this.validationRules = {
            email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            phone: /^[\+]?[1-9][\d]{0,15}$/,
            url: /^https?:\/\/.+/,
            date: /^\d{4}-\d{2}-\d{2}$/,
            time: /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/,
            datetime: /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/
        };
        
        this.init();
    }
    
    init() {
        // Add validation to all forms
        const forms = document.querySelectorAll('form[data-validate="true"]');
        forms.forEach(form => this.attachValidation(form));
        
        // Real-time validation on input
        document.addEventListener('input', (e) => {
            if (e.target.hasAttribute('data-validate')) {
                this.validateField(e.target);
            }
        });
        
        // Validation on form submission
        document.addEventListener('submit', (e) => {
            if (e.target.hasAttribute('data-validate')) {
                if (!this.validateForm(e.target)) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            }
        });
    }
    
    attachValidation(form) {
        form.classList.add('needs-validation');
        form.setAttribute('novalidate', 'true');
    }
    
    validateField(field) {
        const rules = field.dataset.validate.split(',');
        let isValid = true;
        let errorMessage = '';
        
        // Clear previous validation state
        field.classList.remove('is-valid', 'is-invalid');
        this.clearFieldError(field);
        
        for (const rule of rules) {
            const validation = this.applyRule(field.value, rule.trim(), field);
            if (!validation.isValid) {
                isValid = false;
                errorMessage = validation.message;
                break;
            }
        }
        
        // Apply validation state
        if (field.value && !isValid) {
            field.classList.add('is-invalid');
            this.showFieldError(field, errorMessage);
        } else if (field.value) {
            field.classList.add('is-valid');
        }
        
        return isValid;
    }
    
    validateForm(form) {
        const fields = form.querySelectorAll('[data-validate]');
        let isFormValid = true;
        
        fields.forEach(field => {
            if (!this.validateField(field)) {
                isFormValid = false;
            }
        });
        
        // Show form-level feedback
        if (!isFormValid) {
            this.showFormError(form, 'Please correct the errors below');
        } else {
            this.clearFormError(form);
        }
        
        return isFormValid;
    }
    
    applyRule(value, rule, field) {
        switch (rule) {
            case 'required':
                return {
                    isValid: value.trim() !== '',
                    message: 'This field is required'
                };
                
            case 'email':
                return {
                    isValid: !value || this.validationRules.email.test(value),
                    message: 'Please enter a valid email address'
                };
                
            case 'phone':
                return {
                    isValid: !value || this.validationRules.phone.test(value),
                    message: 'Please enter a valid phone number'
                };
                
            case 'url':
                return {
                    isValid: !value || this.validationRules.url.test(value),
                    message: 'Please enter a valid URL'
                };
                
            case 'date':
                return {
                    isValid: !value || this.isValidDate(value),
                    message: 'Please enter a valid date (YYYY-MM-DD)'
                };
                
            case 'time':
                return {
                    isValid: !value || this.validationRules.time.test(value),
                    message: 'Please enter a valid time (HH:MM)'
                };
                
            case 'datetime':
                return {
                    isValid: !value || this.isValidDateTime(value),
                    message: 'Please enter a valid date and time'
                };
                
            case 'future-date':
                return {
                    isValid: !value || new Date(value) > new Date(),
                    message: 'Date must be in the future'
                };
                
            case 'past-date':
                return {
                    isValid: !value || new Date(value) < new Date(),
                    message: 'Date must be in the past'
                };
                
            default:
                if (rule.startsWith('min-length:')) {
                    const minLength = parseInt(rule.split(':')[1]);
                    return {
                        isValid: !value || value.length >= minLength,
                        message: `Minimum length is ${minLength} characters`
                    };
                }
                if (rule.startsWith('max-length:')) {
                    const maxLength = parseInt(rule.split(':')[1]);
                    return {
                        isValid: !value || value.length <= maxLength,
                        message: `Maximum length is ${maxLength} characters`
                    };
                }
                return { isValid: true, message: '' };
        }
    }
    
    isValidDate(dateString) {
        const date = new Date(dateString);
        return date instanceof Date && !isNaN(date) && dateString.match(this.validationRules.date);
    }
    
    isValidDateTime(datetimeString) {
        const datetime = new Date(datetimeString);
        return datetime instanceof Date && !isNaN(datetime);
    }
    
    showFieldError(field, message) {
        let errorElement = field.parentNode.querySelector('.invalid-feedback');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'invalid-feedback';
            field.parentNode.appendChild(errorElement);
        }
        errorElement.textContent = message;
    }
    
    clearFieldError(field) {
        const errorElement = field.parentNode.querySelector('.invalid-feedback');
        if (errorElement) {
            errorElement.remove();
        }
    }
    
    showFormError(form, message) {
        let errorElement = form.querySelector('.form-error');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'alert alert-danger form-error';
            form.insertBefore(errorElement, form.firstChild);
        }
        errorElement.textContent = message;
    }
    
    clearFormError(form) {
        const errorElement = form.querySelector('.form-error');
        if (errorElement) {
            errorElement.remove();
        }
    }
}

// Initialize form validation when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new FormValidator();
});

// Export for use in other modules
window.FormValidator = FormValidator;
