class DashboardScenarios extends DashboardMetrics {
    constructor() {
        super();
        // Initialize managers
        this.statusMessage = new StatusMessageManager();
        this.saveStatus = new SaveStatusManager();
        this.draftManager = new DraftManager();
        this.scenarioManager = null; // Will be initialized with userId
        this.userId = null; // Will be fetched from API
        this.autoSaveTimer = null;
    }
    
    async fetchUserId() {
        /** Fetch user ID from authenticated user. */
        try {
            const response = await fetch('/api/current-user');
            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Authentication required. Please log in.');
                }
                throw new Error(`Failed to fetch user ID: ${response.status}`);
            }
            const userData = await response.json();
            if (!userData.user_id) {
                throw new Error('User ID not found in response');
            }
            return userData.user_id;
        } catch (error) {
            console.error('Error fetching user ID:', error);
            throw error;
        }
    }

    // Delegate status messages to StatusMessageManager
    showStatusMessage(message, type = 'info') {
        this.statusMessage.show(message, type);
    }
    
    // Delegate save status to SaveStatusManager
    updateSaveStatus(status = 'none') {
        this.saveStatus.update(status);
    }
    
    async initializeScenarioManagement() {
        // Fetch authenticated user ID
        try {
            this.userId = await this.fetchUserId();
        } catch (error) {
            console.error('Failed to initialize scenario management:', error);
            this.showStatusMessage(error.message || 'Failed to initialize. Please refresh the page.', 'error');
            return;
        }
        
        this.scenarioManager = new ScenarioManager(this.userId, this.statusMessage, this.saveStatus);
        this.draftManager = new DraftManager(this.userId);
        
        await this.scenarioManager.loadScenarios();
        
        const defaultScenario = this.scenarioManager.getDefaultScenario();
        if (defaultScenario) {
            await this.loadScenario(defaultScenario.scenario_id);
        } else {
            this.activeCapabilities.clear();
            await this.recalculateMetrics();
            // Offer to restore local draft if present when no scenario is selected
            try {
                if (this.draftManager.hasDraft() && !this.scenarioManager.getCurrentScenarioId()) {
                    if (confirm('A local worksheet draft was found. Restore it?')) {
                        await this.restoreDraft();
                        this.updateSaveStatus('unsaved');
                    }
                }
            } catch (e) {
                console.warn('Draft restore check failed:', e);
            }
            this.updateButtonStates();
        }
    }
    
    async loadScenarios() {
        // Ensure userId is available
        if (!this.userId) {
            try {
                this.userId = await this.fetchUserId();
            } catch (error) {
                console.error('Failed to load scenarios:', error);
                this.showStatusMessage(error.message || 'Authentication required', 'error');
                return;
            }
        }
        
        if (!this.scenarioManager) {
            this.scenarioManager = new ScenarioManager(this.userId, this.statusMessage, this.saveStatus);
        }
        try {
            await this.scenarioManager.loadScenarios();
            // Keep scenarios property for backward compatibility
            this.scenarios = this.scenarioManager.scenarios;
            this.updateButtonStates();
        } catch (error) {
            console.error('Error loading scenarios:', error);
            this.updateButtonStates();
        }
    }
    
    async loadScenario(scenarioId) {
        // Ensure userId is available
        if (!this.userId) {
            try {
                this.userId = await this.fetchUserId();
            } catch (error) {
                console.error('Failed to load scenario:', error);
                this.showStatusMessage(error.message || 'Authentication required', 'error');
                return;
            }
        }
        
        if (!this.scenarioManager) {
            this.scenarioManager = new ScenarioManager(this.userId, this.statusMessage, this.saveStatus);
        }
        
        if (!scenarioId) {
            this.scenarioManager.setCurrentScenarioId(null);
            // Keep currentScenarioId for backward compatibility
            this.currentScenarioId = null;
            this.activeCapabilities.clear();
            if (this.activeControls) {
                this.activeControls.clear();
            }
            this.createVerticalTree();
            if (typeof this.updateDebugInfo === 'function') {
                this.updateDebugInfo();
            }
            await this.recalculateMetrics();
            this.updateSaveStatus('none');
            this.updateButtonStates();
            return;
        }
        
        try {
            const scenario = await this.scenarioManager.loadScenario(scenarioId);
            this.scenarioManager.setCurrentScenarioId(scenarioId);
            // Keep currentScenarioId for backward compatibility
            this.currentScenarioId = scenarioId;
            
            // Ensure activeCapabilities is initialized
            if (!this.activeCapabilities) {
                this.activeCapabilities = new Set();
            }
            this.activeCapabilities.clear();
            
            // Only activate capabilities that were explicitly saved with is_active=true in the scenario
            scenario.selections.forEach(selection => {
                if (selection.is_active) {
                    this.activeCapabilities.add(selection.capability_id);
                }
            });
            
            // Ensure activeControls is initialized before restoring control selections
            if (!this.activeControls) {
                this.activeControls = new Set();
            }
            this.activeControls.clear();
            
            // Ensure treeData is loaded before restoring control selections
            if (!this.treeData) {
                try {
                    const response = await fetch('/api/capability-tree');
                    if (response.ok) {
                        this.treeData = await response.json();
                    }
                } catch (e) {
                    console.warn('Failed to load treeData during scenario load:', e);
                }
            }
            
            // Load control selections if available
            if (scenario.control_selections && scenario.control_selections.length > 0) {
                // Scenario has explicit control selections - restore them
                scenario.control_selections.forEach(controlSelection => {
                    if (controlSelection.is_active) {
                        this.activeControls.add(controlSelection.control_id);
                    }
                });
            } else {
                // Scenario has no control selections - default to activating all controls from active capabilities
                if (this.treeData) {
                    this.activeCapabilities.forEach(capabilityId => {
                        const capability = this.treeData.find(cap => cap.capability_id === capabilityId);
                        if (capability && capability.controls) {
                            capability.controls.forEach(control => {
                                this.activeControls.add(control.control_id);
                            });
                        }
                    });
                }
            }
            
            this.createVerticalTree();
            if (typeof this.updateDebugInfo === 'function') {
                this.updateDebugInfo();
            }
            await this.recalculateMetrics();
            
            this.updateSaveStatus('saved');
            
            // Update scenario selector to show the loaded scenario
            const selector = document.getElementById('scenario-selector');
            if (selector) {
                selector.value = scenarioId.toString();
            }
            
            this.updateButtonStates();
            
            this.showStatusMessage(`Loaded scenario: ${scenario.scenario_name}`, 'success');
        } catch (error) {
            console.error('Error loading scenario:', error);
            this.showStatusMessage('Error loading scenario', 'error');
            this.updateButtonStates();
        }
    }
    
    updateButtonStates() {
        /** Update button states based on current scenario selection. */
        const deleteBtn = document.getElementById('delete-scenario-btn');
        const saveBtn = document.getElementById('save-scenario-btn');
        
        const hasScenario = this.scenarioManager && this.scenarioManager.getCurrentScenarioId();
        
        if (deleteBtn) {
            if (hasScenario) {
                deleteBtn.disabled = false;
                deleteBtn.style.opacity = '1';
                deleteBtn.style.cursor = 'pointer';
            } else {
                deleteBtn.disabled = true;
                deleteBtn.style.opacity = '0.5';
                deleteBtn.style.cursor = 'not-allowed';
            }
        }
        
        // Save button can always be used (it will prompt for name if no scenario)
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.style.opacity = '1';
            saveBtn.style.cursor = 'pointer';
        }
    }
    
    serializeSelections() {
        // Ensure activeCapabilities is initialized
        if (!this.activeCapabilities) {
            this.activeCapabilities = new Set();
        }
        
        // Ensure treeData is available
        if (!this.treeData) {
            console.warn('serializeSelections: treeData is not available');
            return {
                selections: [],
                control_selections: []
            };
        }
        
        const capabilitySelections = this.treeData.map(cap => ({
            capability_id: cap.capability_id,
            is_active: this.activeCapabilities.has(cap.capability_id)
        }));
        
        const controlSelections = this.serializeControlSelections ? this.serializeControlSelections() : [];
        
        return {
            selections: capabilitySelections,
            control_selections: controlSelections
        };
    }

    // Draft management methods
    getDraftKey() {
        return this.draftManager.getDraftKey();
    }

    hasDraft() {
        return this.draftManager.hasDraft();
    }

    persistDraft() {
        const success = this.draftManager.persistDraft(this.activeCapabilities, this.activeControls);
        if (success) {
            this.updateSaveStatus('saved');
        } else {
            this.updateSaveStatus('error');
        }
    }

    async restoreDraft() {
        const draftData = this.draftManager.restoreDraft();
        if (!draftData) {
            return;
        }
        
        this.activeCapabilities = new Set(draftData.activeCapabilityIds || []);
        this.activeControls = new Set(draftData.activeControlIds || []);
        this.createVerticalTree();
        if (typeof this.updateDebugInfo === 'function') {
            this.updateDebugInfo();
        }
        await this.recalculateMetrics();
    }

    clearDraft() {
        this.draftManager.clearDraft();
    }

    async saveScenario() {
        if (!this.scenarioManager || !this.scenarioManager.getCurrentScenarioId()) {
            this.showStatusMessage('No worksheet selected. Use Save As… to name and save, or continue editing to keep a local draft.', 'warning');
            // Persist local draft immediately for safety
            this.persistDraft();
            return;
        }
        
        this.updateSaveStatus('saving');
        
        try {
            const selections = this.serializeSelections();
            
            await this.scenarioManager.updateScenario(this.scenarioManager.getCurrentScenarioId(), selections);
            
            this.updateSaveStatus('saved');
            this.showStatusMessage('Scenario saved successfully', 'success');
            // Clear any lingering draft once saved to a named worksheet
            this.clearDraft();
            
        } catch (error) {
            console.error('Error saving scenario:', error);
            this.updateSaveStatus('error');
            this.showStatusMessage(error.message || 'Error saving scenario', 'error');
        }
    }

    scheduleAutoSave() {
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        
        this.updateSaveStatus('unsaved');
        
        this.autoSaveTimer = setTimeout(() => {
            // Save to server if a worksheet is selected, otherwise persist local draft
            if (this.scenarioManager && this.scenarioManager.getCurrentScenarioId()) {
                this.saveScenario();
            } else {
                this.persistDraft();
            }
        }, 2000);
    }
    
    async activateAllCapabilities() {
        if (!this.treeData) {
            console.warn('activateAllCapabilities: treeData is null');
            return;
        }
        
        // Set all capabilities to active
        let activatedCount = 0;
        let skippedCount = 0;
        this.treeData.forEach(cap => {
            if (cap && cap.capability_id) {
                this.activeCapabilities.add(cap.capability_id);
                // Activate all controls when activating capability
                if (cap.controls) {
                    cap.controls.forEach(control => {
                        if (this.activeControls) {
                            this.activeControls.add(control.control_id);
                        }
                    });
                }
                activatedCount++;
            } else {
                skippedCount++;
            }
        });
        
        // Update UI first to reflect the new active state
        this.createVerticalTree();
        if (typeof this.updateDebugInfo === 'function') {
            this.updateDebugInfo();
        }
        
        // CRITICAL FIX: Await metrics recalculation to ensure DOM updates properly
        await this.recalculateMetrics();
        
        // Schedule auto-save regardless of selection status
        this.scheduleAutoSave();
        
        // Show status message after everything is updated
        this.showStatusMessage(`All capabilities activated (${activatedCount})`, 'success');
    }
    
    async clearAllCapabilities() {
        if (!this.treeData) {
            return;
        }
        
        // Ensure activeCapabilities is initialized
        if (!this.activeCapabilities) {
            this.activeCapabilities = new Set();
        }
        
        // Ensure activeControls is initialized
        if (!this.activeControls) {
            this.activeControls = new Set();
        }
        
        // Close any open modals that might have stale checkbox states
        const modal = document.getElementById('detailModal');
        if (modal && modal.style.display === 'block') {
            modal.style.display = 'none';
        }
        
        // Clear all capabilities and controls from active sets
        this.activeCapabilities.clear();
        this.activeControls.clear();
        
        // Update UI to reflect the cleared state
        this.createVerticalTree();
        if (typeof this.updateDebugInfo === 'function') {
            this.updateDebugInfo();
        }
        
        // CRITICAL FIX: Await metrics recalculation to ensure DOM updates properly
        await this.recalculateMetrics();
        
        // Schedule auto-save regardless of selection status
        this.scheduleAutoSave();
        
        // Show status message after everything is updated
        this.showStatusMessage('All capabilities deactivated', 'success');
    }
    
    async createNewScenario() {
        const scenarioName = prompt('Enter name for new scenario:');
        if (!scenarioName || !scenarioName.trim()) {
            return;
        }
        
        try {
            // Ensure userId is available
            if (!this.userId) {
                this.userId = await this.fetchUserId();
            }
            
            if (!this.scenarioManager) {
                this.scenarioManager = new ScenarioManager(this.userId, this.statusMessage, this.saveStatus);
            }
            
            const newScenario = await this.scenarioManager.createScenario(scenarioName.trim(), false);
            
            // Load the newly created scenario
            await this.loadScenario(newScenario.scenario_id);
            this.showStatusMessage(`Created and loaded scenario: ${scenarioName}`, 'success');
            // Once user created a new named worksheet, clear any existing draft
            this.clearDraft();
            this.updateButtonStates();
            
        } catch (error) {
            console.error('Error creating scenario:', error);
            this.showStatusMessage(error.message || 'Error creating scenario', 'error');
            this.updateButtonStates();
        }
    }
    
    async deleteScenario() {
        if (!this.scenarioManager || !this.scenarioManager.getCurrentScenarioId()) {
            this.showStatusMessage('No scenario selected to delete', 'warning');
            return;
        }
        
        const scenario = this.scenarioManager.getScenario(this.scenarioManager.getCurrentScenarioId());
        const scenarioName = scenario ? scenario.scenario_name : 'this scenario';
        
        if (!confirm(`Are you sure you want to delete "${scenarioName}"? This action cannot be undone.`)) {
            return;
        }
        
        try {
            await this.scenarioManager.deleteScenario(this.scenarioManager.getCurrentScenarioId());
            
            this.activeCapabilities.clear();
            this.createVerticalTree();
            if (typeof this.updateDebugInfo === 'function') {
                this.updateDebugInfo();
            }
            await this.recalculateMetrics();
            this.updateSaveStatus('none');
            
            this.showStatusMessage(`Deleted scenario: ${scenarioName}`, 'success');
            // Clear draft upon deletion to avoid restoring stale state
            this.clearDraft();
            
            // Clear scenario selection and update UI
            this.scenarioManager.setCurrentScenarioId(null);
            this.currentScenarioId = null;
            
            // Update scenario selector to show no selection
            const selector = document.getElementById('scenario-selector');
            if (selector) {
                selector.value = '';
            }
            
            this.updateButtonStates();
            
        } catch (error) {
            console.error('Error deleting scenario:', error);
            this.showStatusMessage(error.message || 'Error deleting scenario', 'error');
            this.updateButtonStates();
        }
    }

    async saveAsScenario() {
        // Ensure userId is available
        if (!this.userId) {
            try {
                this.userId = await this.fetchUserId();
            } catch (error) {
                console.error('Failed to save scenario:', error);
                this.showStatusMessage(error.message || 'Authentication required', 'error');
                return;
            }
        }
        
        if (!this.scenarioManager) {
            this.scenarioManager = new ScenarioManager(this.userId, this.statusMessage, this.saveStatus);
        }
        
        const defaultName = this.scenarioManager.generateSuggestedWorksheetName();
        const scenarioName = prompt('Enter worksheet name:', defaultName);
        if (!scenarioName || !scenarioName.trim()) {
            return;
        }
        
        try {
            // Create new scenario
            const newScenario = await this.scenarioManager.createScenario(scenarioName.trim(), false);

            // Persist current selections to the new scenario
            const selections = this.serializeSelections();
            await this.scenarioManager.updateScenario(newScenario.scenario_id, selections);

            // Refresh UI to select and load the new scenario
            await this.scenarioManager.loadScenarios();
            await this.loadScenario(newScenario.scenario_id);
            this.clearDraft();
            this.updateSaveStatus('saved');
            this.updateButtonStates();
            this.showStatusMessage(`Saved as: ${scenarioName.trim()}`, 'success');
        } catch (err) {
            console.error('Save As failed:', err);
            this.updateSaveStatus('error');
            // Show detailed error message to user
            // Check if error message contains duplicate scenario info
            const errorMessage = err.message || err.toString();
            if (errorMessage.includes('already exists') || errorMessage.includes('Scenario name')) {
                // This is a duplicate name error - show the descriptive message directly
                this.showStatusMessage(errorMessage, 'error');
            } else {
                // For other errors, show the error message or a generic fallback
                this.showStatusMessage(errorMessage || 'Save As failed', 'error');
            }
        }
    }
    
    async showMetricDetails(metricType) {
        // Handle assigned-controls separately - fetch all controls and check mapping status
        if (metricType === 'assigned-controls') {
            try {
                // Use the same metrics API to get accurate counts (same source as the panel)
                const activeCapabilityIds = Array.from(this.activeCapabilities || []);
                const metricsResponse = await fetch('/api/capability-analysis', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ capability_ids: activeCapabilityIds })
                });
                if (!metricsResponse.ok) {
                    throw new Error(`HTTP error! status: ${metricsResponse.status}`);
                }
                const metrics = await metricsResponse.json();
                
                const totalControls = metrics.total_controls || 0;
                const mappedCount = metrics.controls_in_capabilities || 0;
                const unmappedCount = totalControls - mappedCount;

                // Fetch all controls to get details for unmapped ones
                const controlsResponse = await fetch('/api/controls?limit=1000');
                if (!controlsResponse.ok) {
                    throw new Error(`HTTP error! status: ${controlsResponse.status}`);
                }
                const allControls = await controlsResponse.json();

                // Fetch mapped control IDs from the same source as metrics (capability_control_mapping table)
                const mappedResponse = await fetch('/api/controls/mapped');
                if (!mappedResponse.ok) {
                    throw new Error(`HTTP error! status: ${mappedResponse.status}`);
                }
                const mappedData = await mappedResponse.json();
                const mappedControlIds = new Set(mappedData.mapped_control_ids || []);

                // Separate controls into mapped and unmapped
                const unmappedControls = [];

                allControls.forEach(control => {
                    const controlId = control.id || control.control_id;
                    const isMapped = mappedControlIds.has(controlId);
                    
                    if (!isMapped) {
                        unmappedControls.push({
                            id: controlId,
                            title: control.title || control.control_title || '',
                            description: control.description || control.control_description || ''
                        });
                    }
                });

                // Build modal content with only unmapped controls
                let content = `<h2>Unmapped Controls</h2>`;
                content += `<div style="margin-bottom: 1rem; padding: 0.75rem; background: #f0f0f0; border-radius: 4px;">`;
                content += `<strong>Total Controls:</strong> ${totalControls} | `;
                content += `<strong>Mapped to Capabilities:</strong> ${mappedCount} | `;
                content += `<strong>Unmapped:</strong> ${unmappedCount}`;
                content += `</div>`;

                // Unmapped Controls Section
                content += `<div style="margin-bottom: 2rem;">`;
                content += `<h3 style="color: #6c757d; margin-bottom: 0.75rem; border-bottom: 2px solid #6c757d; padding-bottom: 0.5rem;">Unmapped Controls (${unmappedCount})</h3>`;
                
                if (unmappedCount > 0 && unmappedControls.length > 0) {
                    content += '<div style="max-height: 500px; overflow-y: auto;">';
                    content += '<table class="data-table" style="width: 100%; border-collapse: collapse;">';
                    content += '<thead><tr>';
                    content += '<th style="padding: 8px; border-bottom: 2px solid #ddd; background-color: #f5f5f5;">Control ID</th>';
                    content += '<th style="padding: 8px; border-bottom: 2px solid #ddd; background-color: #f5f5f5;">Control Title</th>';
                    content += '<th style="padding: 8px; border-bottom: 2px solid #ddd; background-color: #f5f5f5;">Description</th>';
                    content += '</tr></thead><tbody>';

                    unmappedControls.slice(0, 100).forEach((control) => {
                        content += '<tr>';
                        content += `<td style="padding: 8px; border-bottom: 1px solid #eee;">${control.id || ''}</td>`;
                        content += `<td style="padding: 8px; border-bottom: 1px solid #eee;">${control.title || ''}</td>`;
                        const desc = control.description || '';
                        const snippet = desc.length > 160 ? `${desc.substring(0, 160)}...` : desc;
                        content += `<td style="padding: 8px; border-bottom: 1px solid #eee;">${snippet}</td>`;
                        content += '</tr>';
                    });

                    content += '</tbody></table>';
                    if (unmappedCount > 100) {
                        content += `<div style="padding: 10px; font-style: italic; color: #999;">... and ${unmappedCount - 100} more unmapped controls</div>`;
                    }
                    content += '</div>';
                } else {
                    content += '<p style="color: #666; font-style: italic;">All controls are mapped to capabilities.</p>';
                }
                content += '</div>';

                const modal = document.getElementById('detailModal');
                const modalBody = document.getElementById('modalBody');
                if (modal && modalBody) {
                    modalBody.innerHTML = content;
                    modal.style.display = 'block';
                }
            } catch (err) {
                console.error('Error showing assigned controls details:', err);
                this.showStatusMessage('Failed to load assigned controls details', 'error');
            }
            return;
        }

        // Always derive lists from the capability-analysis API so we have precise,
        // up-to-date items that reflect the current active capability selection.
        try {
            // Ensure activeCapabilities is initialized
            if (!this.activeCapabilities) {
                this.activeCapabilities = new Set();
            }
            
            const activeCapabilityIds = Array.from(this.activeCapabilities || []);
            
            const response = await fetch('/api/capability-analysis', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ capability_ids: activeCapabilityIds })
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const analysis = await response.json();

            let title = '';
            let items = [];
            let expectedCount = 0;
            
            if (metricType === 'active-controls') {
                title = 'Active Controls';
                items = analysis.active_controls_list || [];
                expectedCount = analysis.active_controls || 0;
            } else if (metricType === 'partially-covered') {
                title = 'Risks with Partial Control Coverage';
                items = analysis.partially_covered_risks_list || [];
                expectedCount = analysis.partially_covered_risks || 0;
            } else if (metricType === 'exposed-risks') {
                title = 'Exposed Risks (No Active Controls)';
                items = analysis.exposed_risks_list || [];
                expectedCount = analysis.exposed_risks || 0;
            } else {
                this.showStatusMessage('Unknown metric type', 'warning');
                return;
            }

            // Validate that the list length matches the expected count
            if (items.length !== expectedCount) {
                console.warn(
                    `⚠️ Data mismatch for ${metricType}: list has ${items.length} items but count shows ${expectedCount}. ` +
                    `Using count from API response.`
                );
                // Ensure we only show the correct number of items
                // This prevents showing stale or incorrect data
                if (items.length > expectedCount) {
                    items = items.slice(0, expectedCount);
                }
            }

            // If nothing to show, inform the user and exit gracefully
            if (!items || items.length === 0) {
                this.showStatusMessage(`No items found for ${title}`, 'info');
                return;
            }

            // Normalize items into a common shape for rendering
            const normalized = items.map((it) => {
                return {
                    id: it.id || it.risk_id || it.control_id || it.capability_id,
                    title: it.title || it.risk_title || it.control_title || it.capability_name,
                    description: it.description || it.risk_description || it.control_description || ''
                };
            });

            // Determine column headers based on metric type
            let idHeader = 'ID';
            let titleHeader = 'Title';
            if (metricType === 'exposed-risks' || metricType === 'partially-covered') {
                idHeader = 'Risk ID';
                titleHeader = 'Risk Title';
            } else if (metricType === 'active-controls') {
                idHeader = 'Control ID';
                titleHeader = 'Control Title';
            }

            // Use expectedCount for the title to match the metric panel
            // This ensures consistency even if there's a data mismatch
            let content = `<h2>${title} (${expectedCount})</h2>`;
            content += '<div style="max-height: 400px; overflow-y: auto;">';
            content += '<table class="data-table" style="width: 100%; border-collapse: collapse;">';
            content += '<thead><tr>';
            content += `<th style="padding: 8px; border-bottom: 2px solid #ddd; background-color: #f5f5f5;">${idHeader}</th>`;
            content += `<th style="padding: 8px; border-bottom: 2px solid #ddd; background-color: #f5f5f5;">${titleHeader}</th>`;
            content += `<th style="padding: 8px; border-bottom: 2px solid #ddd; background-color: #f5f5f5;">Description</th>`;
            content += '</tr></thead>';
            content += '<tbody>';

            normalized.slice(0, 100).forEach((item) => {
                content += '<tr>';
                content += `<td style="padding: 8px; border-bottom: 1px solid #eee;">${item.id || ''}</td>`;
                content += `<td style="padding: 8px; border-bottom: 1px solid #eee;">${item.title || ''}</td>`;
                const desc = item.description || '';
                const snippet = desc.length > 160 ? `${desc.substring(0, 160)}...` : desc;
                content += `<td style="padding: 8px; border-bottom: 1px solid #eee;">${snippet}</td>`;
                content += '</tr>';
            });

            content += '</tbody></table>';

            // Show "more" message based on expectedCount to match the metric
            if (expectedCount > 100) {
                content += `<div style="padding: 10px; font-style: italic; color: #999;">... and ${expectedCount - 100} more</div>`;
            }

            content += '</div>';

            const modal = document.getElementById('detailModal');
            const modalBody = document.getElementById('modalBody');
            if (modal && modalBody) {
                modalBody.innerHTML = content;
                modal.style.display = 'block';
            }
        } catch (err) {
            console.error('Error showing metric details:', err);
            this.showStatusMessage('Failed to load details for this metric', 'error');
        }
    }
}
