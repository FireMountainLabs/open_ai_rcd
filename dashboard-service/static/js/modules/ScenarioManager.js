class ScenarioManager {
    constructor(userId, statusMessageManager, saveStatusManager) {
        this.userId = userId;
        this.statusMessage = statusMessageManager;
        this.saveStatus = saveStatusManager;
        this.scenarios = [];
        this.currentScenarioId = null;
    }

    async loadScenarios() {
        try {
            const response = await fetch(`/api/capability-scenarios?user_id=${this.userId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            this.scenarios = await response.json();
            
            const selector = document.getElementById('scenario-selector');
            if (selector) {
                selector.innerHTML = '<option value="">-- Select Scenario --</option>';
                this.scenarios.forEach(scenario => {
                    const option = document.createElement('option');
                    option.value = scenario.scenario_id;
                    option.textContent = scenario.scenario_name + (scenario.is_default ? ' (Default)' : '');
                    selector.appendChild(option);
                });
            }
            return this.scenarios;
        } catch (error) {
            console.error('Error loading scenarios:', error);
            throw error;
        }
    }

    async loadScenario(scenarioId) {
        if (!scenarioId) {
            this.currentScenarioId = null;
            return null;
        }
        
        try {
            const response = await fetch(`/api/capability-scenarios/${scenarioId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const scenario = await response.json();
            this.currentScenarioId = scenarioId;
            return scenario;
        } catch (error) {
            console.error('Error loading scenario:', error);
            throw error;
        }
    }

    async createScenario(scenarioName, isDefault = false) {
        try {
            const response = await fetch('/api/capability-scenarios', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    scenario_name: scenarioName.trim(),
                    is_default: isDefault
                })
            });
            
            if (!response.ok) {
                const errorDetail = await this.extractErrorDetail(response);
                // For 400 errors (like duplicate names), use the descriptive message directly
                // Check for duplicate name errors in the message
                if (response.status === 400 && (errorDetail.includes('already exists') || errorDetail.includes('Scenario name'))) {
                    throw new Error(errorDetail);
                } else if (response.status === 400) {
                    // Other 400 errors - show the error detail directly
                    throw new Error(errorDetail);
                } else {
                    throw new Error(`Failed to create scenario: ${errorDetail}`);
                }
            }
            
            const newScenario = await response.json();
            await this.loadScenarios();
            return newScenario;
        } catch (error) {
            console.error('Error creating scenario:', error);
            throw error;
        }
    }

    async updateScenario(scenarioId, selections) {
        try {
            const response = await fetch(`/api/capability-scenarios/${scenarioId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(selections)
            });

            if (!response.ok) {
                const errorDetail = await this.extractErrorDetail(response);
                throw new Error(`Failed to save selections: ${errorDetail}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error updating scenario:', error);
            throw error;
        }
    }

    async deleteScenario(scenarioId) {
        try {
            const response = await fetch(`/api/capability-scenarios/${scenarioId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            if (this.currentScenarioId === scenarioId) {
                this.currentScenarioId = null;
            }
            await this.loadScenarios();
            return true;
        } catch (error) {
            console.error('Error deleting scenario:', error);
            throw error;
        }
    }

    async extractErrorDetail(response) {
        let errorDetail = `HTTP error! status: ${response.status}`;
        try {
            const errorText = await response.text();
            if (errorText) {
                try {
                    const errorBody = JSON.parse(errorText);
                    // Try multiple possible error message fields
                    if (errorBody.detail) {
                        errorDetail = Array.isArray(errorBody.detail) 
                            ? errorBody.detail.map(e => `${e.loc?.join('.')}: ${e.msg}`).join('; ')
                            : (errorBody.detail || errorDetail);
                    } else if (errorBody.error) {
                        errorDetail = errorBody.error || errorDetail;
                    } else if (errorBody.message) {
                        errorDetail = errorBody.message || errorDetail;
                    } else {
                        // Use the text if it's not empty
                        errorDetail = errorText.trim() || errorDetail;
                    }
                } catch (e) {
                    // Not JSON, use text as-is if it's not empty
                    errorDetail = errorText.trim() || errorDetail;
                }
            }
        } catch (e) {
            // If we can't get the text, use a default message
            console.error('Error extracting error detail:', e);
            errorDetail = `Request failed with status ${response.status}`;
        }
        
        // Ensure we never return an empty string
        if (!errorDetail || !errorDetail.trim()) {
            errorDetail = `Request failed with status ${response.status}`;
        }
        
        return errorDetail;
    }

    getDefaultScenario() {
        return this.scenarios.find(s => s.is_default);
    }

    getScenario(scenarioId) {
        return this.scenarios.find(s => s.scenario_id === scenarioId);
    }

    getCurrentScenarioId() {
        return this.currentScenarioId;
    }

    setCurrentScenarioId(scenarioId) {
        this.currentScenarioId = scenarioId;
    }

    generateSuggestedWorksheetName() {
        const pad = (n) => n.toString().padStart(2, '0');
        const d = new Date();
        return `${d.getFullYear()}.${pad(d.getMonth()+1)}.${pad(d.getDate())}.${pad(d.getHours())}.${pad(d.getMinutes())}.${pad(d.getSeconds())}_capability_worksheet`;
    }
}

