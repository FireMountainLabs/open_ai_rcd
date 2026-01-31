class DashboardMetrics extends DashboardTreeRenderer {
    constructor() {
        super();
        // Track previous metric values to detect changes
        this.previousMetrics = {
            active_controls: null,
            exposed_risks: null,
            partially_covered_risks: null,
            active_risks: null
        };
        // Track capabilities with unique controls
        this.capabilitiesWithUniqueControls = new Set();
        this.uniqueControlCounts = {}; // Map of capability_id -> unique_control_count
        this.uniqueControlIds = {}; // Map of capability_id -> Set of unique control IDs
    }
    
    // Helper to animate metric change
    // colorType: 'green', 'yellow', 'red'
    animateMetricChange(element, changeValue, colorType) {
        if (!element) return;
        
        // Remove any existing change indicator
        const existingChange = element.parentElement.querySelector('.metric-change-indicator');
        if (existingChange) {
            existingChange.remove();
        }
        
        // Map color types to actual colors
        const colorMap = {
            'green': { color: '#28a745', background: '#d4edda' },
            'yellow': { color: '#ffc107', background: '#fff3cd' },
            'red': { color: '#dc3545', background: '#f8d7da' }
        };
        
        const colors = colorMap[colorType] || colorMap['green'];
        
        // Create change indicator
        const changeIndicator = document.createElement('div');
        changeIndicator.className = 'metric-change-indicator';
        changeIndicator.textContent = changeValue > 0 ? `+${changeValue}` : `${changeValue}`;
        changeIndicator.style.cssText = `
            position: absolute;
            right: 10px;
            top: 10px;
            font-size: 1rem;
            font-weight: bold;
            color: ${colors.color};
            background: ${colors.background};
            padding: 4px 8px;
            border-radius: 4px;
            animation: slideInFadeOut 2s ease-out forwards;
            z-index: 10;
            pointer-events: none;
        `;
        
        // Make parent position relative if not already
        const parent = element.parentElement;
        if (window.getComputedStyle(parent).position === 'static') {
            parent.style.position = 'relative';
        }
        
        parent.appendChild(changeIndicator);
        
        // Flash the metric value - keep it black at rest, only show color during animation
        element.style.transition = 'all 0.3s ease';
        element.style.transform = 'scale(1.1)';
        element.style.color = colors.color;
        
        setTimeout(() => {
            element.style.transform = 'scale(1)';
            element.style.color = '#212529'; // Always return to black
        }, 300);
    }
    
    async recalculateMetrics() {
        try {
            // Get list of active capability IDs
            const activeCapabilityIds = Array.from(this.activeCapabilities);
            
            // Get list of active control IDs if available
            const activeControlIds = this.activeControls ? Array.from(this.activeControls) : null;
            
            const requestPayload = {
                capability_ids: activeCapabilityIds
            };
            
            // Include control_ids only if we have actual granular control selections
            // Don't send empty array - backend interprets that as filtering to zero controls
            if (activeControlIds !== null && activeControlIds.length > 0) {
                requestPayload.control_ids = activeControlIds;
            }
            
            
            // Add cache-busting timestamp to prevent any caching issues
            const response = await fetch('/api/capability-analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache'
                },
                body: JSON.stringify(requestPayload),
                cache: 'no-store'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const metrics = await response.json();
            
            // Update metric cards
            const totalCapabilitiesEl = document.getElementById('metric-total-capabilities');
            const assignedControlsEl = document.getElementById('metric-assigned-controls');
            const activeControlsEl = document.getElementById('metric-active-controls');
            const partiallyCoveredEl = document.getElementById('metric-partially-covered-risks');
            const exposedRisksEl = document.getElementById('metric-exposed-risks');
            
            if (totalCapabilitiesEl) {
                const value = this.treeData ? this.treeData.length : 0;
                totalCapabilitiesEl.textContent = value;
                totalCapabilitiesEl.setAttribute('data-value', value);
            } else {
                console.warn('⚠️ metric-total-capabilities element not found');
            }
            
            if (assignedControlsEl) {
                const text = `${metrics.controls_in_capabilities || 0} / ${metrics.total_controls || 0}`;
                assignedControlsEl.textContent = text;
                assignedControlsEl.setAttribute('data-value', text);
            } else {
                console.warn('⚠️ metric-assigned-controls element not found');
            }
            
            if (activeControlsEl) {
                const value = metrics.active_controls || 0;
                const previous = this.previousMetrics.active_controls;
                
                // Show change if this is not the first update
                if (previous !== null && previous !== value) {
                    const change = value - previous;
                    // Green for increase (good - activating controls), Yellow for decrease (bad - deactivating)
                    const colorType = change > 0 ? 'green' : 'yellow';
                    this.animateMetricChange(activeControlsEl, change, colorType);
                }
                
                activeControlsEl.textContent = value;
                activeControlsEl.style.color = '#212529'; // Always black at rest
                activeControlsEl.setAttribute('data-value', value);
                activeControlsEl.dispatchEvent(new Event('change', { bubbles: true }));
                this.previousMetrics.active_controls = value;
            } else {
                console.warn('⚠️ metric-active-controls element not found');
            }
            
            // Track previous values before updating for partially covered logic
            const prevExposed = this.previousMetrics.exposed_risks;
            const prevActiveRisks = this.previousMetrics.active_risks;
            const prevPartially = this.previousMetrics.partially_covered_risks;
            
            if (partiallyCoveredEl) {
                const value = metrics.partially_covered_risks || 0;
                const previous = prevPartially;
                
                // Show change if this is not the first update
                if (previous !== null && previous !== value) {
                    const change = value - previous;
                    const newExposed = metrics.exposed_risks || 0;
                    const newActiveRisks = metrics.active_risks || 0;
                    const exposedChange = prevExposed !== null ? (newExposed - prevExposed) : 0;
                    const activeRisksChange = prevActiveRisks !== null ? (newActiveRisks - prevActiveRisks) : 0;
                    
                    let colorType = 'green'; // Default
                    
                    // User requirements for Partially Covered Risks:
                    // - If fully exposed risk transitions to partial covered: Green +n (good)
                    // - If a fully controlled risk goes partial: Yellow +n (bad - losing full coverage)
                    // - If partially goes fully covered: Green -n (good - gaining full coverage)
                    // - Yellow for negative change (but check context)
                    
                    if (change > 0) {
                        // Partially increased (+n): Could be from exposed (good) or from fully covered (bad)
                        if (exposedChange < 0) {
                            // Exposed decreased, partially increased: Good (exposed → partially)
                            colorType = 'green';
                        } else if (activeRisksChange < 0) {
                            // Active risks decreased, partially increased: Bad (fully covered → partially)
                            colorType = 'yellow';
                        } else {
                            // Unknown transition, but partially increased
                            // Default to yellow as it's losing full coverage
                            colorType = 'yellow';
                        }
                    } else {
                        // Partially decreased (-n): Could be to fully covered (good) or to exposed (bad)
                        if (activeRisksChange > 0) {
                            // Active risks increased, partially decreased: Good (partially → fully covered)
                            colorType = 'green';
                        } else if (exposedChange > 0) {
                            // Exposed increased, partially decreased: Bad (partially → exposed)
                            // But wait - exposed should show red +n, not partial
                            // This case shouldn't happen if we're tracking correctly, but handle it
                            colorType = 'yellow'; // Show as yellow negative change
                        } else {
                            // Unknown transition, but partially decreased
                            // Default to green as gaining full coverage is more likely
                            colorType = 'green';
                        }
                    }
                    
                    this.animateMetricChange(partiallyCoveredEl, change, colorType);
                }
                
                partiallyCoveredEl.textContent = value;
                partiallyCoveredEl.style.color = '#212529'; // Always black at rest
                partiallyCoveredEl.setAttribute('data-value', value);
                partiallyCoveredEl.dispatchEvent(new Event('change', { bubbles: true }));
                this.previousMetrics.partially_covered_risks = value;
            } else {
                console.warn('⚠️ metric-partially-covered-risks element not found');
            }
            
            if (exposedRisksEl) {
                const newValue = String(metrics.exposed_risks || 0);
                const previous = prevExposed;
                const value = parseInt(newValue);
                
                // Show change if this is not the first update
                if (previous !== null && previous !== value) {
                    const change = value - previous;
                    // Red for increase (bad - more exposed), Green for decrease (good - fewer exposed)
                    const colorType = change > 0 ? 'red' : 'green';
                    this.animateMetricChange(exposedRisksEl, change, colorType);
                }
                
                exposedRisksEl.textContent = newValue;
                exposedRisksEl.innerText = newValue;
                exposedRisksEl.style.color = '#212529'; // Always black at rest
                exposedRisksEl.setAttribute('data-value', newValue);
                exposedRisksEl.dispatchEvent(new Event('change', { bubbles: true }));
                exposedRisksEl.dispatchEvent(new Event('input', { bubbles: true }));
                this.previousMetrics.exposed_risks = value;
            } else {
                console.warn('⚠️ metric-exposed-risks element not found');
            }
            
            // Update previous active_risks
            this.previousMetrics.active_risks = metrics.active_risks || 0;
            
            // Show summary of changes in status message
            if (this.previousMetrics.active_controls !== null) {
                const changes = this.calculateMetricChanges(metrics);
                if (changes.hasChanges) {
                    this.showMetricChangeSummary(changes);
                }
            }
            
            // Identify and highlight capabilities with unique controls
            // Do this after metrics update to avoid blocking
            this.identifyUniqueControlCapabilities().catch(err => {
                console.warn('Error identifying unique controls:', err);
            });
            
        } catch (error) {
            console.error('Error recalculating metrics:', error);
            this.showError('Could not update metrics.');
        }
    }
    
    async identifyUniqueControlCapabilities() {
        if (!this.treeData || this.treeData.length === 0) return;
        
        try {
            // Fetch unique control analysis
            const response = await fetch('/api/capability-unique-controls');
            if (!response.ok) {
                console.warn('Could not fetch unique controls data');
                this.capabilitiesWithUniqueControls = new Set();
                return;
            }
            
            const uniqueControlsData = await response.json();
            this.capabilitiesWithUniqueControls = new Set(uniqueControlsData.capabilities_with_unique_controls || []);
            this.uniqueControlCounts = uniqueControlsData.unique_control_counts || {};
            // Store mapping of capability_id -> Set of unique control IDs
            this.uniqueControlIds = {};
            if (uniqueControlsData.unique_control_ids) {
                for (const [capabilityId, controlIds] of Object.entries(uniqueControlsData.unique_control_ids)) {
                    this.uniqueControlIds[capabilityId] = new Set(controlIds);
                }
            }
            
            // Re-render tree to apply highlighting
            if (typeof this.createVerticalTree === 'function') {
                this.createVerticalTree();
            }
            
        } catch (error) {
            console.warn('Could not identify unique control capabilities:', error);
            this.capabilitiesWithUniqueControls = new Set();
            this.uniqueControlIds = {};
        }
    }
    
    calculateMetricChanges(newMetrics) {
        const changes = {
            hasChanges: false,
            active_controls: newMetrics.active_controls - (this.previousMetrics.active_controls || 0),
            exposed_risks: newMetrics.exposed_risks - (this.previousMetrics.exposed_risks || 0),
            partially_covered_risks: newMetrics.partially_covered_risks - (this.previousMetrics.partially_covered_risks || 0),
            active_risks: (newMetrics.active_risks || 0) - (this.previousMetrics.active_risks || 0)
        };
        
        changes.hasChanges = changes.active_controls !== 0 || 
                            changes.exposed_risks !== 0 || 
                            changes.partially_covered_risks !== 0 ||
                            changes.active_risks !== 0;
        
        return changes;
    }
    
    showMetricChangeSummary(changes) {
        if (!changes.hasChanges) return;
        
        const parts = [];
        if (changes.active_controls !== 0) {
            parts.push(`${changes.active_controls > 0 ? '+' : ''}${changes.active_controls} controls`);
        }
        if (changes.exposed_risks !== 0) {
            parts.push(`${changes.exposed_risks > 0 ? '+' : ''}${changes.exposed_risks} exposed risks`);
        }
        if (changes.partially_covered_risks !== 0) {
            parts.push(`${changes.partially_covered_risks > 0 ? '+' : ''}${changes.partially_covered_risks} partial risks`);
        }
        if (changes.active_risks !== 0) {
            parts.push(`${changes.active_risks > 0 ? '+' : ''}${changes.active_risks} covered risks`);
        }
        
        if (parts.length > 0 && typeof this.showStatusMessage === 'function') {
            const message = `Metrics updated: ${parts.join(', ')}`;
            this.showStatusMessage(message, 'info');
        }
    }
}
