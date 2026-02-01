/**
 * Visualization Manager Module
 * Handles all visualization rendering and interactions
 */

class VisualizationManager extends BaseModule {
    constructor(dataManager) {
        super('VisualizationManager');
        this.dataManager = dataManager;
        this.currentZoom = d3.zoomIdentity;
        this.zoomBehavior = null;
    }

    /**
     * Render overview dashboard
     */
    renderOverview() {
        this.logger.info('Rendering overview');
        
        const data = this.dataManager.data;
        if (!data) {
            this.showError('No data available for overview');
            return;
        }

        this.renderOverviewCards(data);
        this.renderLastUpdated(data);
    }

    /**
     * Render overview cards
     * @param {Object} data - Complete dataset
     */
    renderOverviewCards(data) {
        const cardsContainer = document.querySelector('.overview-cards');
        if (!cardsContainer) return;

        const cards = [
            {
                title: 'Risks',
                count: data.risks?.details?.length || 0,
                color: '#ffbf00',
                clickable: true,
                tab: 'risks'
            },
            {
                title: 'Controls', 
                count: data.controls?.details?.length || 0,
                color: '#00b0f0',
                clickable: true,
                tab: 'controls'
            },
            {
                title: 'Questions',
                count: data.questions?.details?.length || 0,
                color: '#6f30a0',
                clickable: true,
                tab: 'questions'
            },
            {
                title: 'Unmapped Risks',
                count: data.gaps?.summary?.unmapped_risks || 0,
                color: '#dc2626',
                clickable: true,
                tab: 'gaps',
                gapType: 'risks'
            }
        ];

        cardsContainer.innerHTML = cards.map(card => `
            <div class="overview-card ${card.clickable ? 'clickable-overview-card' : ''}" 
                 ${card.clickable ? `data-tab="${card.tab}"` : ''}
                 ${card.gapType ? `data-gap-type="${card.gapType}"` : ''}>
                <div class="card-header">
                    <h3>${card.title}</h3>
                </div>
                <div class="card-content">
                    <div class="count-display" style="color: ${card.color}">
                        ${card.count.toLocaleString()}
                    </div>
                </div>
            </div>
        `).join('');

        // Add click handlers
        cardsContainer.querySelectorAll('.clickable-overview-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const tab = e.currentTarget.dataset.tab;
                const gapType = e.currentTarget.dataset.gapType;
                
                if (gapType) {
                    this.switchGapsTab(gapType);
                } else {
                    this.switchTab(tab);
                }
            });
        });
    }

    /**
     * Render last updated information
     * @param {Object} data - Complete dataset
     */
    renderLastUpdated(data) {
        const lastUpdatedContainer = document.querySelector('.last-updated');
        if (!lastUpdatedContainer) return;

        // This would be populated from API call to /api/last-updated
        lastUpdatedContainer.innerHTML = `
            <div class="last-updated-item">
                <strong>RISKS LAST UPDATED:</strong> ${new Date().toLocaleString()} (v6)
            </div>
            <div class="last-updated-item">
                <strong>CONTROLS LAST UPDATED:</strong> ${new Date().toLocaleString()} (v4)
            </div>
            <div class="last-updated-item">
                <strong>QUESTIONS LAST UPDATED:</strong> ${new Date().toLocaleString()} (v0)
            </div>
        `;
    }

    /**
     * Render network visualization
     * @param {string} layout - Layout type ('force')
     */
    async renderNetwork(layout = 'force') {
        this.logger.info(`Rendering network with ${layout} layout`);
        
        const container = document.getElementById('networkContainer');
        if (!container) return;

        const width = container.clientWidth;
        const height = container.clientHeight;

        // Clear container
        container.innerHTML = '';

        const svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        if (layout === 'force') {
            await this.renderForceLayout(svg, width, height);
        }
    }

    /**
     * Render force-directed network layout
     * @param {Object} svg - D3 SVG selection
     * @param {number} width - Container width
     * @param {number} height - Container height
     */
    async renderForceLayout(svg, width, height) {
        const data = this.dataManager.data;
        if (!data?.network) {
            this.showError('No network data available');
            return;
        }

        // Implementation would go here - keeping it simple for now
        svg.append('text')
            .attr('x', width / 2)
            .attr('y', height / 2)
            .attr('text-anchor', 'middle')
            .style('font-size', '16px')
            .text('Force layout visualization');
    }


    /**
     * Switch to a specific tab
     * @param {string} tabName - Tab name to switch to
     */
    switchTab(tabName) {
        this.logger.info(`Switching to tab: ${tabName}`);
        
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Show/hide content sections
        document.querySelectorAll('.tab-content').forEach(section => {
            section.style.display = section.id === `${tabName}Content` ? 'block' : 'none';
        });

        this.currentTab = tabName;

        // Render tab-specific content
        switch (tabName) {
            case 'overview':
                this.renderOverview();
                break;
            case 'risks':
                this.renderRisks();
                break;
            case 'controls':
                this.renderControls();
                break;
            case 'questions':
                this.renderQuestions();
                break;
            case 'relationships':
                this.renderNetwork('force');
                break;
        }
    }

    /**
     * Render risks table
     */
    renderRisks() {
        const data = this.dataManager.data;
        if (!data?.risks?.details) {
            this.showError('No risks data available');
            return;
        }

        const tbody = document.querySelector('#risksTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        data.risks.details.forEach((risk, index) => {
            const row = document.createElement('tr');
            const controlBadgeClass = risk.control_count === 0 ? 'count-badge zero-count' : 'count-badge';
            const questionBadgeClass = risk.question_count === 0 ? 'count-badge zero-count' : 'count-badge';
            
            row.innerHTML = `
                <td class="risk-number">${index + 1}</td>
                <td class="risk-id">${risk.risk_id}</td>
                <td>${risk.risk_title}</td>
                <td><span class="${controlBadgeClass}">${risk.control_count}</span></td>
                <td><span class="${questionBadgeClass}">${risk.question_count}</span></td>
            `;
            row.addEventListener('click', () => this.showDetailModal('risk', risk));
            tbody.appendChild(row);
        });
    }

    /**
     * Render controls table
     */
    renderControls() {
        const data = this.dataManager.data;
        if (!data?.controls?.details) {
            this.showError('No controls data available');
            return;
        }

        const tbody = document.querySelector('#controlsTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        data.controls.details.forEach((control, index) => {
            const row = document.createElement('tr');
            const riskBadgeClass = control.risk_count === 0 ? 'count-badge zero-count' : 'count-badge';
            const questionBadgeClass = control.question_count === 0 ? 'count-badge zero-count' : 'count-badge';
            
            row.innerHTML = `
                <td class="control-number">${index + 1}</td>
                <td class="control-id">${control.control_id}</td>
                <td>${control.control_title}</td>
                <td><span class="${riskBadgeClass}">${control.risk_count}</span></td>
                <td><span class="${questionBadgeClass}">${control.question_count}</span></td>
            `;
            row.addEventListener('click', () => this.showDetailModal('control', control));
            tbody.appendChild(row);
        });
    }

    /**
     * Render questions table
     */
    renderQuestions() {
        const data = this.dataManager.data;
        if (!data?.questions?.details) {
            this.showError('No questions data available');
            return;
        }

        const tbody = document.querySelector('#questionsTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        data.questions.details.forEach((question, index) => {
            const row = document.createElement('tr');
            const riskBadgeClass = question.risk_count === 0 ? 'count-badge zero-count' : 'count-badge';
            
            row.innerHTML = `
                <td class="question-number">${index + 1}</td>
                <td class="question-id">${question.question_id}</td>
                <td>${question.question_text.substring(0, 100)}${question.question_text.length > 100 ? '...' : ''}</td>
                <td>${question.category}</td>
                <td>-</td>
                <td><span class="${riskBadgeClass}">${question.risk_count}</span></td>
            `;
            row.addEventListener('click', () => this.showDetailModal('question', question));
            tbody.appendChild(row);
        });
    }

    /**
     * Show detail modal for an entity
     * @param {string} type - Entity type
     * @param {Object} item - Entity data
     */
    async showDetailModal(type, item) {
        const modal = document.getElementById('detailModal');
        const modalBody = document.getElementById('modalBody');
        
        if (!modal || !modalBody) return;

        modalBody.innerHTML = '<div class="loading">Loading detailed information...</div>';
        modal.style.display = 'block';
        
        try {
            const itemId = item.id || item.risk_id || item.control_id || item.question_id;
            if (!itemId) {
                modalBody.innerHTML = '<div class="error">Error: Unable to identify the item ID.</div>';
                return;
            }
            
            const detailData = await this.dataManager.getEntityDetail(type, itemId);
            
            if (detailData.error) {
                modalBody.innerHTML = `<div class="error">Error: ${detailData.error}</div>`;
                return;
            }
            
            modalBody.innerHTML = this.renderDetailedContent(type, detailData);
            
        } catch (error) {
            this.logger.error('Error fetching detail data:', error);
            modalBody.innerHTML = '<div class="error">Failed to load detailed information.</div>';
        }
    }

    /**
     * Render detailed content for modal
     * @param {string} type - Entity type
     * @param {Object} data - Detailed data
     * @returns {string} HTML content
     */
    renderDetailedContent(type, data) {
        // This would contain the detailed rendering logic
        return `<div class="detail-content">
            <h3>${type.charAt(0).toUpperCase() + type.slice(1)} Details</h3>
            <p>Detailed content would be rendered here.</p>
        </div>`;
    }

    /**
     * Switch gaps tab
     * @param {string} gapType - Type of gap to show
     */
    switchGapsTab(gapType) {
        this.logger.info(`Switching to gaps tab: ${gapType}`);
        // Implementation would go here
    }
}
