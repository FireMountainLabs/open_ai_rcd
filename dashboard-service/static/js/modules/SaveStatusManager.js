class SaveStatusManager {
    constructor() {
        this.saveStatusIcon = null;
        this.statusIndicator = null;
        this.init();
    }

    init() {
        this.saveStatusIcon = document.getElementById('save-status-icon');
        this.statusIndicator = document.querySelector('#save-status-icon .status-indicator');
    }

    update(status = 'none') {
        if (!this.saveStatusIcon || !this.statusIndicator) {
            this.init();
            if (!this.saveStatusIcon || !this.statusIndicator) {
                console.warn('⚠️ Save status icon elements not found');
                return;
            }
        }

        // Remove all status classes
        this.statusIndicator.classList.remove('saved', 'saving', 'error', 'none', 'unsaved');
        
        // Add the current status class
        this.statusIndicator.classList.add(status);
        
        // Update tooltip text based on status
        const tooltips = {
            'saved': 'Saved',
            'saving': 'Saving...',
            'unsaved': 'Unsaved changes',
            'error': 'Save error',
            'none': 'No changes'
        };
        
        this.saveStatusIcon.title = tooltips[status] || 'Unknown status';
    }
}

