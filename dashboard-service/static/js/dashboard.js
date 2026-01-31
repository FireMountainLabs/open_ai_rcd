/**
 * AIML Risk Management Dashboard
 * Initializes the dashboard and brings all modules together.
 */

class AIMLDashboard extends DashboardEventHandlers {
    constructor() {
        super();
        this.init();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new AIMLDashboard();
});
