class DashboardControls extends DashboardNetwork {
    renderControls() {
        const tbody = document.querySelector('#controlsTable tbody');
        tbody.innerHTML = '';

        this.data.controls.details.forEach((control, index) => {
            const row = document.createElement('tr');
            const riskBadgeClass = control.risk_count === 0 ? 'count-badge zero-count' : 'count-badge';
            const questionBadgeClass = control.question_count === 0 ? 'count-badge zero-count' : 'count-badge';
            
            row.innerHTML = `
                <td class="control-number">${index + 1}</td>
                <td class="control-id">${control.control_id}</td>
                <td>${control.control_title}</td>
                <td>${control.control_description}</td>
                <td><span class="${riskBadgeClass}">${control.risk_count}</span></td>
                <td><span class="${questionBadgeClass}">${control.question_count}</span></td>
            `;
            row.addEventListener('click', () => this.showDetailModal('control', control));
            tbody.appendChild(row);
        });

        if (this.definitionHoverManager) {
            this.definitionHoverManager.enhanceContent(tbody, 'controls');
        }
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Show/hide content sections
        document.querySelectorAll('.tab-content').forEach(section => {
            // HTML has id="overview", id="risks", etc. (not "overviewContent")
            const sectionId = section.id;
            const matchId = sectionId === tabName;
            section.style.display = matchId ? 'block' : 'none';
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
            case 'definitions':
                this.renderDefinitions();
                break;
            case 'relationships':
                this.renderNetwork('force');
                break;
            case 'gaps':
                this.renderGaps();
                break;
            case 'capability-configuration':
            case 'capabilities':
                this.renderCapabilities().catch(error => {
                    console.error('Error rendering capabilities:', error);
                });
                break;
        }
    }
    
    renderOverview() {
        if (!this.data) {
            console.error('❌ No data available to render overview');
            return;
        }
        
        // Update the SOURCES section with last updated times
        this.updateLastUpdatedTimes();
        
        // Render the gap counts in the overview section
        this.renderGaps();
        
        // Update the overview card counts directly (they're already in the HTML)
        const totalRisks = this.data.risks?.details?.length || 0;
        const totalControls = this.data.controls?.details?.length || 0;
        const totalQuestions = this.data.questions?.details?.length || 0;
        
        const totalRisksEl = document.getElementById('totalRisks');
        const totalControlsEl = document.getElementById('totalControls');
        const totalQuestionsEl = document.getElementById('totalQuestions');
        
        if (totalRisksEl) {
            totalRisksEl.textContent = totalRisks.toLocaleString();
            const riskCoverageEl = document.getElementById('riskCoverage');
            if (riskCoverageEl && this.data.gaps?.summary) {
                riskCoverageEl.textContent = `${this.data.gaps.summary.risk_coverage_pct || 0}% coverage`;
            }
        } else {
            console.error('❌ totalRisks element NOT FOUND');
        }
        
        if (totalControlsEl) {
            totalControlsEl.textContent = totalControls.toLocaleString();
            const controlUtilEl = document.getElementById('controlUtilization');
            if (controlUtilEl && this.data.gaps?.summary) {
                controlUtilEl.textContent = `${this.data.gaps.summary.control_utilization_pct || 0}% utilized`;
            }
        } else {
            console.error('❌ totalControls element NOT FOUND');
        }
        
        if (totalQuestionsEl) {
            totalQuestionsEl.textContent = totalQuestions.toLocaleString();
            const questionCovEl = document.getElementById('questionCoverage');
            if (questionCovEl && this.data.gaps?.summary) {
                questionCovEl.textContent = `${this.data.gaps.summary.question_coverage_pct || 0}% coverage`;
            }
        } else {
            console.error('❌ totalQuestions element NOT FOUND');
        }
        
        // NOTE: Cards are already in HTML with correct structure and classes
        // We've updated their count values (totalRisks, totalControls, totalQuestions) above
    }
    
    renderRisks() {
        const tbody = document.querySelector('#risksTable tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        this.data.risks.details.forEach((risk, index) => {
            const row = document.createElement('tr');
            const controlBadgeClass = (risk.control_count || 0) === 0 ? 'count-badge zero-count' : 'count-badge';
            const questionBadgeClass = (risk.question_count || 0) === 0 ? 'count-badge zero-count' : 'count-badge';
            
            row.innerHTML = `
                <td class="risk-number">${index + 1}</td>
                <td class="risk-id">${risk.risk_id}</td>
                <td class="risk-title">${risk.risk_title}</td>
                <td class="risk-controls"><span class="${controlBadgeClass}">${risk.control_count || 0}</span></td>
                <td class="risk-questions"><span class="${questionBadgeClass}">${risk.question_count || 0}</span></td>
            `;
            row.addEventListener('click', () => this.showDetailModal('risk', risk));
            tbody.appendChild(row);
        });
        
        if (this.definitionHoverManager) {
            this.definitionHoverManager.enhanceContent(tbody, 'risks');
        }
    }
    
    renderQuestions() {
        const tbody = document.querySelector('#questionsTable tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        this.data.questions.details.forEach((question, index) => {
            const row = document.createElement('tr');
            const riskBadgeClass = (question.risk_count || 0) === 0 ? 'count-badge zero-count' : 'count-badge';
            const controlBadgeClass = (question.control_count || 0) === 0 ? 'count-badge zero-count' : 'count-badge';
            row.innerHTML = `
                <td class="question-number">${index + 1}</td>
                <td class="question-id">${question.question_id}</td>
                <td>${question.question_text.substring(0, 100)}...</td>
                <td>${question.category || ''}</td>
                <td>${question.managing_role || ''}</td>
                <td><span class="${riskBadgeClass}">${question.risk_count || 0}</span></td>
                <td><span class="${controlBadgeClass}">${question.control_count || 0}</span></td>
            `;
            row.addEventListener('click', () => this.showDetailModal('question', question));
            tbody.appendChild(row);
        });
        
        if (this.definitionHoverManager) {
            this.definitionHoverManager.enhanceContent(tbody, 'questions');
        }
    }
    
    renderDefinitions() {
        this.filterDefinitions();
    }
    
    filterDefinitions() {
        const categoryFilter = document.getElementById('definitionCategoryFilter')?.value || '';
        const letterFilter = this.currentLetterFilter || '';

        if (!this.data.definitions) return;

        // First filter by category
        const categoryFilteredDefinitions = this.data.definitions.filter(definition => {
            return !categoryFilter || definition.category === categoryFilter;
        });

        // Update letter availability based on category-filtered results
        this.updateLetterAvailabilityForFilteredData(categoryFilteredDefinitions);

        // Then filter by letter
        const filteredDefinitions = categoryFilteredDefinitions.filter(definition => {
            return !letterFilter || (definition.term && definition.term.toUpperCase().startsWith(letterFilter));
        });

        const tbody = document.querySelector('#definitionsTable tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (filteredDefinitions.length === 0) {
            const row = document.createElement('tr');
            const message = letterFilter ? 
                `No definitions found for the selected category and letter "${letterFilter}"` : 
                'No definitions found for the selected category';
            row.innerHTML = `<td colspan="6" class="no-data">${message}</td>`;
            tbody.appendChild(row);
            return;
        }

        filteredDefinitions.forEach((definition, index) => {
            const row = document.createElement('tr');
            
            row.innerHTML = `
                <td class="definition-number">${index + 1}</td>
                <td class="definition-term"><strong>${definition.term}</strong></td>
                <td class="definition-title">${definition.title || '-'}</td>
                <td class="definition-description">${definition.description ? definition.description.substring(0, 150) + (definition.description.length > 150 ? '...' : '') : '-'}</td>
                <td class="definition-category">${definition.category || '-'}</td>
                <td class="definition-source">${definition.source || '-'}</td>
            `;
            row.addEventListener('click', () => this.showDetailModal('definition', definition));
            tbody.appendChild(row);
        });
        
        // Enhance content with definition hovers
        if (this.definitionHoverManager) {
            this.definitionHoverManager.enhanceContent(tbody, 'definitions');
        }
    }
    
    setLetterFilter(letter) {
        // Check if the letter link is disabled
        const letterLink = document.querySelector(`.letter-link[data-letter="${letter}"]`);
        if (letterLink && letterLink.classList.contains('disabled')) {
            return; // Don't process disabled letters
        }
        
        // Update the current letter filter
        this.currentLetterFilter = letter;
        
        // Update active state of letter links
        document.querySelectorAll('.letter-link').forEach(link => {
            link.classList.remove('active');
            if (link.dataset.letter === letter) {
                link.classList.add('active');
            }
        });
        
        // Re-filter definitions
        this.filterDefinitions();
    }

    updateLetterAvailability() {
        if (!this.data.definitions) return;
        this.updateLetterAvailabilityForFilteredData(this.data.definitions);
    }

    updateLetterAvailabilityForFilteredData(filteredDefinitions) {
        if (!filteredDefinitions) return;
        
        // Get all unique first letters from filtered definitions
        const availableLetters = new Set();
        filteredDefinitions.forEach(definition => {
            if (definition.term && definition.term.length > 0) {
                const firstLetter = definition.term.toUpperCase().charAt(0);
                if (firstLetter >= 'A' && firstLetter <= 'Z') {
                    availableLetters.add(firstLetter);
                }
            }
        });
        
        // Update letter link states
        document.querySelectorAll('.letter-link').forEach(link => {
            const letter = link.dataset.letter;
            
            // Always enable "All" link
            if (letter === '') {
                link.classList.remove('disabled');
                return;
            }
            
            // Enable/disable based on availability
            if (availableLetters.has(letter)) {
                link.classList.remove('disabled');
            } else {
                link.classList.add('disabled');
            }
        });
    }
    
    async renderCapabilities() {
        // activeCapabilities is now always initialized in DashboardCore constructor
        // Check if this is the first load: empty Set + no current scenario = first load
        // This distinguishes between "never loaded" (empty Set + no scenario) and "user cleared all" (empty Set + scenario exists)
        const isFirstLoad = this.activeCapabilities.size === 0 && !this.currentScenarioId;
        
        // Initialize other properties if they don't exist
        if (!this.selectedType) {
            this.selectedType = '';
        }
        if (!this.selectedDomain) {
            this.selectedDomain = '';
        }
        if (!this.searchTerm) {
            this.searchTerm = '';
        }
        if (!this.sortBy) {
            this.sortBy = 'type-name';
        }
        
        // Load capability tree data if not already loaded
        if (!this.treeData) {
            try {
                const response = await fetch('/api/capability-tree');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                this.treeData = await response.json();
                
                if (!this.treeData || this.treeData.length === 0) {
                    console.warn('API returned empty capability array');
                    this.showError('No capability data available. Please check if capabilities have been loaded into the database.');
                    return;
                }
                
                // Enable all capabilities by default ONLY on the very first load
                // If activeCapabilities is empty and no scenario is loaded, it means this is the first time
                // If it's an empty Set with a scenario, the user has cleared all - don't re-enable
                if (isFirstLoad) {
                    this.treeData.forEach(cap => {
                        if (cap && cap.capability_id) {
                            this.activeCapabilities.add(cap.capability_id);
                        }
                    });
                }
            } catch (error) {
                console.error('Error loading capability tree data:', error);
                this.showError(`Failed to load capability data: ${error.message}`);
                return;
            }
        }
        
        // Setup SVG if not already set up
        if (!this.svg || !this.treeGroup) {
            this.width = this.width || 1400;
            this.height = this.height || 600;
            this.setupSVG();
        }
        
        // Initialize scenario management if not already initialized
        if (!this.scenariosInitialized && typeof this.initializeScenarioManagement === 'function') {
            await this.initializeScenarioManagement();
            this.scenariosInitialized = true;
        }
        
        // Populate domain filter if it exists
        if (typeof this.populateDomainFilter === 'function') {
            this.populateDomainFilter();
        }
        
        // Render the tree
        if (typeof this.createVerticalTree === 'function') {
            this.createVerticalTree();
        }
        
        // Load unique controls information after tree is rendered
        if (typeof this.identifyUniqueControlCapabilities === 'function') {
            // Delay slightly to ensure tree is rendered first
            setTimeout(() => {
                this.identifyUniqueControlCapabilities();
            }, 100);
        }
        
        // Update debug info if method exists
        if (typeof this.updateDebugInfo === 'function') {
            this.updateDebugInfo();
        }
        
        // Re-attach filter event listeners since they're in this tab
        // Use a small delay to ensure DOM is updated
        setTimeout(() => {
            const searchFilter = document.getElementById('search-filter');
            if (searchFilter && !searchFilter.hasAttribute('data-listener-attached')) {
                searchFilter.addEventListener('input', (e) => {
                    if (typeof this.filterBySearch === 'function') {
                        this.filterBySearch(e.target.value);
                    }
                });
                searchFilter.setAttribute('data-listener-attached', 'true');
            }
            
            const clearSearchBtn = document.getElementById('clear-search');
            if (clearSearchBtn && !clearSearchBtn.hasAttribute('data-listener-attached')) {
                clearSearchBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (typeof this.clearSearch === 'function') {
                        this.clearSearch();
                    }
                });
                clearSearchBtn.setAttribute('data-listener-attached', 'true');
            }
            
            const typeFilter = document.getElementById('capability-type-filter');
            if (typeFilter && !typeFilter.hasAttribute('data-listener-attached')) {
                typeFilter.addEventListener('change', (e) => {
                    if (typeof this.filterByType === 'function') {
                        this.filterByType(e.target.value);
                    }
                });
                typeFilter.setAttribute('data-listener-attached', 'true');
            }
            
            const domainFilter = document.getElementById('domain-filter');
            if (domainFilter && !domainFilter.hasAttribute('data-listener-attached')) {
                domainFilter.addEventListener('change', (e) => {
                    if (typeof this.filterByDomain === 'function') {
                        this.filterByDomain(e.target.value);
                    }
                });
                domainFilter.setAttribute('data-listener-attached', 'true');
            }
            
            const sortFilter = document.getElementById('sort-filter');
            if (sortFilter && !sortFilter.hasAttribute('data-listener-attached')) {
                sortFilter.addEventListener('change', (e) => {
                    if (typeof this.sortByOption === 'function') {
                        this.sortByOption(e.target.value);
                    }
                });
                sortFilter.setAttribute('data-listener-attached', 'true');
            }
        }, 100);
    }
}
