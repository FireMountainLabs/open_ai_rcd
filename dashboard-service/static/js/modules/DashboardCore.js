class DashboardCore {
    constructor() {
        this.data = {
            risks: null,
            controls: null,
            questions: null,
            definitions: null,
            network: null,
            gaps: null
        };
        this.currentTab = 'overview';
        this.zoomBehavior = null;
        this.currentZoom = d3.zoomIdentity;
        this.currentLetterFilter = '';
        this.definitionHoverManager = null;
        
        // Initialize activeCapabilities and activeControls to ensure they always exist
        // These are used by DashboardTreeRenderer, DashboardMetrics, and DashboardScenarios
        this.activeCapabilities = new Set();
        this.activeControls = new Set();
        
        // The init call will be moved to the final class constructor
    }

    async init() {
        try {
            await this.loadData();
            this.initializeDefinitionHoverManager();
            this.renderOverview();
            this.setupEventListeners();
        } catch (error) {
            console.error('❌ Error in DashboardCore.init():', error);
        }
    }
    
    setupEventListeners() {
        // This will be overridden by child classes but provides a base
    }

    async loadData() {
        try {
            const [risksRes, controlsRes, questionsRes, definitionsRes, networkRes, gapsRes, lastUpdatedRes, managingRolesRes] = await Promise.all([
                fetch('/api/risks/summary'),
                fetch('/api/controls/summary'),
                fetch('/api/questions/summary'),
                fetch('/api/definitions'),
                fetch('/api/network'),
                fetch('/api/gaps'),
                fetch('/api/last-updated'),
                fetch('/api/managing-roles')
            ]);

            this.data.risks = await risksRes.json();
            this.data.controls = await controlsRes.json();
            this.data.questions = await questionsRes.json();
            this.data.definitions = await definitionsRes.json();
            this.data.network = await networkRes.json();
            this.data.gaps = await gapsRes.json();
            this.data.lastUpdated = await lastUpdatedRes.json();
            this.data.managingRoles = await managingRolesRes.json();

            this.populateFilters();
            this.updateLastUpdatedTimes();
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Failed to load data. Please refresh the page.');
        }
    }
    
    initializeDefinitionHoverManager() {
        if (typeof DefinitionHoverManager !== 'undefined' && this.data.definitions) {
            this.definitionHoverManager = new DefinitionHoverManager(this);
            this.definitionHoverManager.updateDefinitions(this.data.definitions);
        }
    }

    populateFilters() {
        const questionCategoryFilter = document.getElementById('questionCategoryFilter');
        questionCategoryFilter.innerHTML = '<option value="">All Managing Roles</option>';
        
        if (this.data.managingRoles && this.data.managingRoles.managing_roles) {
            this.data.managingRoles.managing_roles.forEach(role => {
                const option = document.createElement('option');
                option.value = role;
                option.textContent = role;
                questionCategoryFilter.appendChild(option);
            });
        }

        const definitionCategoryFilter = document.getElementById('definitionCategoryFilter');
        definitionCategoryFilter.innerHTML = '<option value="">All Categories</option>';
        
        if (this.data.definitions && this.data.definitions.length > 0) {
            const categories = [...new Set(this.data.definitions.map(def => def.category).filter(cat => cat))];
            categories.sort().forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                definitionCategoryFilter.appendChild(option);
            });
        }
    }

    updateLastUpdatedTimes() {
        if (!this.data.lastUpdated) {
            return;
        }
        
        const formatDateTime = (dateTimeStr) => {
            if (!dateTimeStr) return 'Unknown';
            const date = new Date(dateTimeStr);
            return date.toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        };

        const risksElement = document.getElementById('risksLastUpdated');
        const controlsElement = document.getElementById('controlsLastUpdated');
        const questionsElement = document.getElementById('questionsLastUpdated');
        const definitionsElement = document.getElementById('definitionsLastUpdated');
        const risksVersionElement = document.getElementById('risksVersion');
        const controlsVersionElement = document.getElementById('controlsVersion');
        const questionsVersionElement = document.getElementById('questionsVersion');
        const definitionsVersionElement = document.getElementById('definitionsVersion');
        
        if (risksElement && this.data.lastUpdated.risks) {
            risksElement.textContent = formatDateTime(this.data.lastUpdated.risks.last_updated);
        } else if (risksElement && this.data.lastUpdated.risks_updated) {
            // Fallback for old API format
            risksElement.textContent = formatDateTime(this.data.lastUpdated.risks_updated);
        }
        if (risksVersionElement) {
            risksVersionElement.textContent = this.data.lastUpdated.risks?.version || this.data.lastUpdated.risksVersion || 'unknown';
        }
        
        if (controlsElement && this.data.lastUpdated.controls) {
            controlsElement.textContent = formatDateTime(this.data.lastUpdated.controls.last_updated);
        } else if (controlsElement && this.data.lastUpdated.controls_updated) {
            // Fallback for old API format
            controlsElement.textContent = formatDateTime(this.data.lastUpdated.controls_updated);
        }
        if (controlsVersionElement) {
            controlsVersionElement.textContent = this.data.lastUpdated.controls?.version || this.data.lastUpdated.controlsVersion || 'unknown';
        }
        
        if (questionsElement && this.data.lastUpdated.questions) {
            questionsElement.textContent = formatDateTime(this.data.lastUpdated.questions.last_updated);
        } else if (questionsElement && this.data.lastUpdated.questions_updated) {
            // Fallback for old API format
            questionsElement.textContent = formatDateTime(this.data.lastUpdated.questions_updated);
        }
        if (questionsVersionElement) {
            questionsVersionElement.textContent = this.data.lastUpdated.questions?.version || this.data.lastUpdated.questionsVersion || 'unknown';
        }
        
        if (definitionsElement && this.data.lastUpdated.definitions) {
            definitionsElement.textContent = formatDateTime(this.data.lastUpdated.definitions.last_updated);
        } else if (definitionsElement && this.data.lastUpdated.definitions_updated) {
            // Fallback for old API format
            definitionsElement.textContent = formatDateTime(this.data.lastUpdated.definitions_updated);
        }
        if (definitionsVersionElement) {
            definitionsVersionElement.textContent = this.data.lastUpdated.definitions?.version || this.data.lastUpdated.definitionsVersion || 'unknown';
        }
    }
    
    showError(message) {
        // Try multiple possible error element IDs for backward compatibility
        const errorElement = document.getElementById('error-message') || 
                            document.getElementById('error') || 
                            document.getElementById('status-message');
        
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        } else {
            // Fallback: log to console if no error element found
            console.error('Error:', message);
        }
    }
    
    async showDetailModal(type, item) {
        // Check if we're already in a modal (for stacking)
        const existingModal = document.querySelector('.modal[style*="display: block"]');
        const isStacking = existingModal !== null;
        
        let modal, modalBody;
        
        if (isStacking) {
            // Create a new modal for stacking
            const stackedModal = this.createStackedModal();
            modal = stackedModal.modal;
            modalBody = stackedModal.modalBody;
        } else {
            // Use the existing modal
            modal = document.getElementById('detailModal');
            modalBody = document.getElementById('modalBody');
        }
        
        // Show loading state
        modalBody.innerHTML = '<div class="loading">Loading detailed information...</div>';
        modal.style.display = 'block';
        
        try {
            let detailData;
            
            // For definitions, we can use the data directly without needing an ID
            if (type === 'definition') {
                detailData = item;
            } else {
                // Handle both search result format (with 'id' field) and table row format (with specific ID fields)
                const itemId = item.id || item.risk_id || item.control_id || item.question_id || item.definition_id;
                
                // Check if we have a valid itemId
                if (!itemId) {
                    modalBody.innerHTML = '<div class="error">Error: Unable to identify the item ID.</div>';
                    return;
                }
                
                // Fetch detailed data from API
                if (type === 'risk') {
                    const response = await fetch(`/api/risk/${itemId}`);
                    detailData = await response.json();
                } else if (type === 'control') {
                    const response = await fetch(`/api/control/${itemId}`);
                    detailData = await response.json();
                } else if (type === 'question') {
                    const response = await fetch(`/api/question/${itemId}`);
                    detailData = await response.json();
                }
            }
            
            if (detailData.error) {
                modalBody.innerHTML = `<div class="error">Error: ${detailData.error}</div>`;
                return;
            }
            
            // Render detailed content
            modalBody.innerHTML = this.renderDetailedContent(type, detailData);
            
            // Enhance modal content with definition hovers for all modal types
            if (this.definitionHoverManager) {
                // Small delay to ensure DOM is fully updated
                setTimeout(() => {
                    this.definitionHoverManager.enhanceContent(modalBody, 'modal');
                }, 10);
            }
            
        } catch (error) {
            console.error('Error fetching detail data:', error);
            modalBody.innerHTML = '<div class="error">Failed to load detailed information.</div>';
        }
    }
    
    createStackedModal() {
        // Count existing modals to calculate z-index
        const existingModals = document.querySelectorAll('.modal');
        const modalCount = existingModals.length;
        const baseZIndex = 2000;
        const newZIndex = baseZIndex + modalCount;
        
        // Create new modal element
        const modal = document.createElement('div');
        modal.className = 'modal stacked-modal';
        modal.style.zIndex = newZIndex.toString();
        
        // Create unique ID for the modal body
        const modalBodyId = `modalBody_${Date.now()}_${modalCount}`;
        
        // Create modal content
        modal.innerHTML = `
            <div class="modal-content">
                <span class="close">&times;</span>
                <div id="${modalBodyId}" class="modal-body"></div>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(modal);
        
        // Setup close handlers
        const closeBtn = modal.querySelector('.close');
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
            // Remove from DOM after animation
            setTimeout(() => {
                if (modal.parentNode) {
                    modal.parentNode.removeChild(modal);
                }
            }, 300);
        });
        
        // Close when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
                setTimeout(() => {
                    if (modal.parentNode) {
                        modal.parentNode.removeChild(modal);
                    }
                }, 300);
            }
        });
        
        return { modal, modalBody: modal.querySelector(`#${modalBodyId}`) };
    }
    
    renderDetailedContent(type, data) {
        if (type === 'risk') {
            return this.renderRiskDetail(data);
        } else if (type === 'control') {
            return this.renderControlDetail(data);
        } else if (type === 'question') {
            return this.renderQuestionDetail(data);
        } else if (type === 'definition') {
            return this.renderDefinitionDetail(data);
        }
        return '<div class="error">Unknown type</div>';
    }
    
    renderRiskDetail(data) {
        const risk = data.risk;
        const controls = data.associated_controls;
        const questions = data.associated_questions;
        
        let content = `
            <h3>${risk.title}</h3>
            <div class="detail-section">
                <div class="detail-label">Risk ID:</div>
                <div class="detail-value">${risk.id}</div>
            </div>
            <div class="detail-section">
                <div class="detail-label">Description:</div>
                <div class="detail-value">${risk.description || 'No description available'}</div>
            </div>
        `;
        
        // Associated Controls Section
        if (controls && controls.length > 0) {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Associated Controls (${controls.length}):</div>
                    <div class="detail-value">
                        <div class="associated-items">
            `;
            controls.forEach(control => {
                content += `
                    <div class="associated-item">
                        <div class="item-header">
                            <strong>${control.id}</strong> - ${control.title}
                        </div>
                        <div class="item-details">
                            <div class="item-description">${control.description || 'No description'}</div>
                            <div class="item-meta">
                                <span class="meta-item">Type: ${control.type || 'N/A'}</span>
                                <span class="meta-item">Function: ${control.domain || 'N/A'}</span>
                                <span class="meta-item">Maturity: ${control.maturity || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            content += `
                        </div>
                    </div>
                </div>
            `;
        } else {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Associated Controls:</div>
                    <div class="detail-value">No controls mapped to this risk</div>
                </div>
            `;
        }
        
        // Associated Questions Section
        if (questions && questions.length > 0) {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Associated Questions (${questions.length}):</div>
                    <div class="detail-value">
                        <div class="associated-items">
            `;
            questions.forEach(question => {
                content += `
                    <div class="associated-item">
                        <div class="item-header">
                            <strong>${question.id}</strong> - ${question.category || 'N/A'}
                        </div>
                        <div class="item-details">
                            <div class="item-description">${question.text}</div>
                            <div class="item-meta">
                                <span class="meta-item">Topic: ${question.topic || 'N/A'}</span>
                                <span class="meta-item">Category: ${question.category || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            content += `
                        </div>
                    </div>
                </div>
            `;
        } else {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Associated Questions:</div>
                    <div class="detail-value">No questions mapped to this risk</div>
                </div>
            `;
        }
        
        return content;
    }
    
    renderControlDetail(data) {
        const control = data.control;
        const risks = data.associated_risks;
        const questions = data.associated_questions;
        const capabilities = data.associated_capabilities;
        
        let content = `
            <h3>${control.title}</h3>
            <div class="detail-section">
                <div class="detail-label">Control ID:</div>
                <div class="detail-value">${control.id}</div>
            </div>
            <div class="detail-section">
                <div class="detail-label">Type:</div>
                <div class="detail-value">${control.type || 'N/A'}</div>
            </div>
            <div class="detail-section">
                <div class="detail-label">Security Function:</div>
                <div class="detail-value">${control.domain || 'N/A'}</div>
            </div>
            <div class="detail-section">
                <div class="detail-label">Maturity Level:</div>
                <div class="detail-value">${control.maturity || 'N/A'}</div>
            </div>
            <div class="detail-section">
                <div class="detail-label">Description:</div>
                <div class="detail-value">${control.description || 'No description available'}</div>
            </div>
        `;
        
        // Associated Risks Section
        if (risks && risks.length > 0) {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Associated Risks (${risks.length}):</div>
                    <div class="detail-value">
                        <div class="associated-items">
            `;
            risks.forEach(risk => {
                content += `
                    <div class="associated-item">
                        <div class="item-header">
                            <strong>${risk.id}</strong> - ${risk.title}
                        </div>
                        <div class="item-details">
                            <div class="item-description">${risk.description || 'No description'}</div>
                            <div class="item-meta">
                                <span class="meta-item">Type: Risk</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            content += `
                        </div>
                    </div>
                </div>
            `;
        } else {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Associated Risks:</div>
                    <div class="detail-value">No risks mapped to this control</div>
                </div>
            `;
        }
        
        // Associated Questions Section
        if (questions && questions.length > 0) {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Associated Questions (${questions.length}):</div>
                    <div class="detail-value">
                        <div class="associated-items">
            `;
            questions.forEach(question => {
                content += `
                    <div class="associated-item">
                        <div class="item-header">
                            <strong>${question.id}</strong> - ${question.category || 'N/A'}
                        </div>
                        <div class="item-details">
                            <div class="item-description">${question.text}</div>
                            <div class="item-meta">
                                <span class="meta-item">Topic: ${question.topic || 'N/A'}</span>
                                <span class="meta-item">Category: ${question.category || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            content += `
                        </div>
                    </div>
                </div>
            `;
        } else {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Associated Questions:</div>
                    <div class="detail-value">No questions mapped to this control</div>
                </div>
            `;
        }
        
        // Associated Parent Capabilities Section
        if (capabilities && capabilities.length > 0) {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Associated Parent Capabilities (${capabilities.length}):</div>
                    <div class="detail-value">
                        <div class="associated-items">
            `;
            capabilities.forEach(capability => {
                content += `
                    <div class="associated-item">
                        <div class="item-header">
                            <strong>${capability.id}</strong> - ${capability.name}
                        </div>
                        <div class="item-details">
                            <div class="item-description">${capability.definition || 'No description'}</div>
                            <div class="item-meta">
                                <span class="meta-item">Type: ${capability.type || 'N/A'}</span>
                                ${capability.domain ? `<span class="meta-item">Domain: ${capability.domain}</span>` : ''}
                            </div>
                        </div>
                    </div>
                `;
            });
            content += `
                        </div>
                    </div>
                </div>
            `;
        } else {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Associated Parent Capabilities:</div>
                    <div class="detail-value">No capabilities mapped to this control</div>
                </div>
            `;
        }
        
        return content;
    }
    
    renderQuestionDetail(data) {
        const question = data.question;
        const risks = data.associated_risks;
        const controls = data.associated_controls;
        
        let content = `
            <h3>Question ${question.id}</h3>
            <div class="detail-section">
                <div class="detail-label">Question Text:</div>
                <div class="detail-value">${question.text}</div>
            </div>
            <div class="detail-section">
                <div class="detail-label">Category:</div>
                <div class="detail-value">${question.category || 'N/A'}</div>
            </div>
            <div class="detail-section">
                <div class="detail-label">Topic:</div>
                <div class="detail-value">${question.topic || 'N/A'}</div>
            </div>
        `;
        
        // Associated Risks Section
        if (risks && risks.length > 0) {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Associated Risks (${risks.length}):</div>
                    <div class="detail-value">
                        <div class="associated-items">
            `;
            risks.forEach(risk => {
                content += `
                    <div class="associated-item">
                        <div class="item-header">
                            <strong>${risk.id}</strong> - ${risk.title}
                        </div>
                        <div class="item-details">
                            <div class="item-description">${risk.description || 'No description'}</div>
                            <div class="item-meta">
                                <span class="meta-item">Type: Risk</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            content += `
                        </div>
                    </div>
                </div>
            `;
        } else {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Associated Risks:</div>
                    <div class="detail-value">No risks mapped to this question</div>
                </div>
            `;
        }
        
        // Associated Controls Section
        if (controls && controls.length > 0) {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Associated Controls (${controls.length}):</div>
                    <div class="detail-value">
                        <div class="associated-items">
            `;
            controls.forEach(control => {
                content += `
                    <div class="associated-item">
                        <div class="item-header">
                            <strong>${control.id}</strong> - ${control.title}
                        </div>
                        <div class="item-details">
                            <div class="item-description">${control.description || 'No description'}</div>
                            <div class="item-meta">
                                <span class="meta-item">Type: ${control.control_type || 'N/A'}</span>
                                <span class="meta-item">Function: ${control.domain || 'N/A'}</span>
                                <span class="meta-item">Maturity: ${control.maturity_level || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            content += `
                        </div>
                    </div>
                </div>
            `;
        } else {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Associated Controls:</div>
                    <div class="detail-value">No controls mapped to this question</div>
                </div>
            `;
        }
        
        return content;
    }
    
    renderDefinitionDetail(data) {
        let content = `
            <h3>${data.title}</h3>
            <div class="detail-section">
                <div class="detail-label">Term:</div>
                <div class="detail-value">${data.title}</div>
            </div>
            <div class="detail-section">
                <div class="detail-label">Definition:</div>
                <div class="detail-value">${data.description || 'No definition available'}</div>
            </div>
            <div class="detail-section">
                <div class="detail-label">Category:</div>
                <div class="detail-value">${data.category || 'N/A'}</div>
            </div>
        `;
        
        if (data.source) {
            content += `
                <div class="detail-section">
                    <div class="detail-label">Source:</div>
                    <div class="detail-value">${data.source}</div>
                </div>
            `;
        }
        
        return content;
    }
}
