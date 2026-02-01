class StatusMessageManager {
    constructor() {
        this.statusDiv = null;
        this.init();
    }

    init() {
        this.statusDiv = document.getElementById('status-message');
    }

    show(message, type = 'info') {
        if (!this.statusDiv) {
            this.init();
            if (!this.statusDiv) {
                return;
            }
        }

        // Clear any existing timeout
        if (this.statusDiv._hideTimeout) {
            clearTimeout(this.statusDiv._hideTimeout);
            this.statusDiv._hideTimeout = null;
        }
        
        // Set text content explicitly
        this.statusDiv.textContent = message;
        this.statusDiv.innerHTML = ''; // Clear any HTML
        const textNode = document.createTextNode(message);
        this.statusDiv.appendChild(textNode);
        
        this.statusDiv.style.display = 'block';
        this.statusDiv.style.padding = '8px 36px 8px 12px'; // Extra padding for close button
        this.statusDiv.style.borderRadius = '4px';
        this.statusDiv.style.position = 'relative';
        this.statusDiv.style.fontSize = '14px';
        this.statusDiv.style.lineHeight = '1.5';
        this.statusDiv.style.maxWidth = '100%';
        this.statusDiv.style.boxSizing = 'border-box';
        
        // Set colors based on type
        this.setStyleForType(type);
        
        // Add close button
        this.ensureCloseButton();
        
        // Auto-hide after timeout (warnings get longer time, errors persist until dismissed)
        this.scheduleAutoHide(type);
    }

    setStyleForType(type) {
        switch(type) {
            case 'success':
                this.statusDiv.style.background = '#d4edda';
                this.statusDiv.style.color = '#155724';
                this.statusDiv.style.border = '1px solid #c3e6cb';
                break;
            case 'error':
                this.statusDiv.style.background = '#f8d7da';
                this.statusDiv.style.color = '#721c24';
                this.statusDiv.style.border = '1px solid #f5c6cb';
                break;
            case 'warning':
                this.statusDiv.style.background = '#fff3cd';
                this.statusDiv.style.color = '#856404';
                this.statusDiv.style.border = '1px solid #ffeaa7';
                break;
            default:
                this.statusDiv.style.background = '#e3f2fd';
                this.statusDiv.style.color = '#1565c0';
                this.statusDiv.style.border = '1px solid #bbdefb';
        }
    }

    ensureCloseButton() {
        let closeBtn = this.statusDiv.querySelector('.status-close-btn');
        if (!closeBtn) {
            closeBtn = document.createElement('button');
            closeBtn.className = 'status-close-btn';
            closeBtn.innerHTML = '×';
            closeBtn.style.cssText = 'position: absolute; top: 4px; right: 8px; background: none; border: none; font-size: 20px; font-weight: bold; cursor: pointer; color: inherit; opacity: 0.6; padding: 0; width: 24px; height: 24px; line-height: 24px; text-align: center;';
            closeBtn.onmouseover = () => closeBtn.style.opacity = '1';
            closeBtn.onmouseout = () => closeBtn.style.opacity = '0.6';
            closeBtn.onclick = () => {
                this.hide();
            };
            this.statusDiv.appendChild(closeBtn);
        }
    }

    scheduleAutoHide(type) {
        if (type === 'success' || type === 'info') {
            this.statusDiv._hideTimeout = setTimeout(() => {
                this.hide();
            }, 3000);
        } else if (type === 'warning') {
            // Warnings auto-hide after 8 seconds
            this.statusDiv._hideTimeout = setTimeout(() => {
                this.hide();
            }, 8000);
        }
        // Errors persist until manually dismissed
    }

    hide() {
        if (this.statusDiv) {
            this.statusDiv.style.display = 'none';
            if (this.statusDiv._hideTimeout) {
                clearTimeout(this.statusDiv._hideTimeout);
                this.statusDiv._hideTimeout = null;
            }
        }
    }
}

