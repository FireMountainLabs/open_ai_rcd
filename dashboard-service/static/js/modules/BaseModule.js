/**
 * Base Module for AIML Visualizer
 * Provides common functionality and error handling for all modules
 */

class BaseModule {
    constructor(name) {
        this.name = name;
        this.config = window.VisualizerConfig || window.DashboardConfig || {};
        this.logger = this.createLogger();
    }

    /**
     * Create a logger instance for this module
     * @returns {Object} Logger with info, warn, error methods
     */
    createLogger() {
        return {
            info: (message, ...args) => {
                // Logging disabled in production - use proper logging service if needed
            },
            warn: (message, ...args) => console.warn(`[${this.name}] ${message}`, ...args),
            error: (message, ...args) => console.error(`[${this.name}] ${message}`, ...args)
        };
    }

    /**
     * Show error message to user
     * @param {string} message - Error message to display
     * @param {string} container - Container selector (optional)
     */
    showError(message, container = '.container') {
        const containerEl = document.querySelector(container);
        if (!containerEl) return;

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.textContent = message;
        containerEl.insertBefore(errorDiv, containerEl.firstChild);
        
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }

    /**
     * Show loading state
     * @param {string} message - Loading message
     * @param {string} container - Container selector
     */
    showLoading(message = 'Loading...', container = '.container') {
        const containerEl = document.querySelector(container);
        if (!containerEl) return;

        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        loadingDiv.textContent = message;
        loadingDiv.id = `${this.name}-loading`;
        containerEl.appendChild(loadingDiv);
    }

    /**
     * Hide loading state
     */
    hideLoading() {
        const loadingEl = document.getElementById(`${this.name}-loading`);
        if (loadingEl) {
            loadingEl.remove();
        }
    }

    /**
     * Safe async operation with error handling
     * @param {Function} operation - Async operation to execute
     * @param {string} errorMessage - Error message to show on failure
     */
    async safeAsync(operation, errorMessage = 'An error occurred') {
        try {
            return await operation();
        } catch (error) {
            this.logger.error(errorMessage, error);
            this.showError(`${errorMessage}: ${error.message}`);
            throw error;
        }
    }

    /**
     * Get configuration value with fallback
     * @param {string} key - Configuration key (supports dot notation)
     * @param {*} defaultValue - Default value if key not found
     * @returns {*} Configuration value or default
     */
    getConfig(key, defaultValue = null) {
        const keys = key.split('.');
        let value = this.config;
        
        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                return defaultValue;
            }
        }
        
        return value;
    }
}
