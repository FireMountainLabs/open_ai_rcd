class DashboardEventHandlers extends DashboardControls {
    setupEventListeners() {
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        const searchInput = document.getElementById('searchInput');
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.performSearch(e.target.value);
            }, window.getConfig('search.debounce_delay', 300));
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                document.getElementById('searchResults').style.display = 'none';
            }
        });

        const modal = document.getElementById('detailModal');
        const closeBtn = document.querySelector('.close');
        
        closeBtn.addEventListener('click', () => modal.style.display = 'none');
        window.addEventListener('click', (e) => {
            if (e.target === modal) modal.style.display = 'none';
        });

        document.querySelectorAll('.clickable-gap-card').forEach(card => {
            card.addEventListener('click', (e) => this.switchGapsTab(e.currentTarget.dataset.gapType));
        });

        // Re-bind after renderOverview creates cards (with delay)
        setTimeout(() => {
            document.querySelectorAll('.clickable-overview-card').forEach(card => {
                card.addEventListener('click', (e) => this.switchTab(e.currentTarget.dataset.tab));
            });
        }, 100);
        
        // Worksheet action buttons (Activate All and Clear All)
        // These buttons are in the capabilities tab, so we attach listeners with a delay
        // to ensure the DOM is fully ready
        setTimeout(() => {
            const activateAllBtn = document.getElementById('activate-all-btn');
            if (activateAllBtn) {
                activateAllBtn.addEventListener('click', async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    await this.activateAllCapabilities();
                });
            } else {
                console.error('❌ activate-all-btn not found in DOM');
            }
            
            const clearAllBtn = document.getElementById('clear-all-btn');
            if (clearAllBtn) {
                clearAllBtn.addEventListener('click', async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    await this.clearAllCapabilities();
                });
            } else {
                console.error('❌ clear-all-btn not found in DOM');
            }
        }, 100);
        
        // Scenario selector
        const scenarioSelector = document.getElementById('scenario-selector');
        if (scenarioSelector) {
            scenarioSelector.addEventListener('change', (e) => this.loadScenario(parseInt(e.target.value)));
        }
        
        // File menu dropdown toggle
        const fileMenuBtn = document.getElementById('file-menu-btn');
        const fileMenu = document.getElementById('file-menu');
        if (fileMenuBtn && fileMenu) {
            fileMenuBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                fileMenu.style.display = fileMenu.style.display === 'none' ? 'block' : 'none';
            });
            
            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!fileMenuBtn.contains(e.target) && !fileMenu.contains(e.target)) {
                    fileMenu.style.display = 'none';
                }
            });
        }
        
        // Scenario management buttons
        const newScenarioBtn = document.getElementById('new-scenario-btn');
        if (newScenarioBtn) {
            newScenarioBtn.addEventListener('click', () => {
                if (fileMenu) fileMenu.style.display = 'none';
                this.createNewScenario();
            });
        }
        
        const saveScenarioBtn = document.getElementById('save-scenario-btn');
        if (saveScenarioBtn) {
            saveScenarioBtn.addEventListener('click', () => {
                if (fileMenu) fileMenu.style.display = 'none';
                if (typeof this.saveAsScenario === 'function') {
                    // Single Save button acts contextually: name draft or save a copy
                    this.saveAsScenario();
                }
            });
        }
        
        const deleteScenarioBtn = document.getElementById('delete-scenario-btn');
        if (deleteScenarioBtn) {
            deleteScenarioBtn.addEventListener('click', () => {
                if (fileMenu) fileMenu.style.display = 'none';
                this.deleteScenario();
            });
        }
        
        // Metric card click handlers
        setTimeout(() => {
            const metricCards = document.querySelectorAll('.clickable-metric');
            metricCards.forEach(card => {
                card.addEventListener('click', () => {
                    const metricType = card.dataset.metricType;
                    this.showMetricDetails(metricType);
                });
            });
        }, 100);
        
        // Definition category filter
        const definitionCategoryFilter = document.getElementById('definitionCategoryFilter');
        if (definitionCategoryFilter) {
            definitionCategoryFilter.addEventListener('change', () => this.filterDefinitions());
        }
        
        // Add letter filter event listeners
        document.querySelectorAll('.letter-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                // Don't process clicks on disabled letters
                if (!e.target.classList.contains('disabled')) {
                    this.setLetterFilter(e.target.dataset.letter);
                }
            });
        });
        
        // Sources panel collapse/expand toggle
        const sourcesHeader = document.querySelector('.sources-header');
        const dataStatus = document.querySelector('.data-status');
        if (sourcesHeader && dataStatus) {
            sourcesHeader.addEventListener('click', () => {
                dataStatus.classList.toggle('collapsed');
            });
        }
        
        // Capability filter event listeners (in capabilities tab)
        // Attach with delay to ensure DOM is ready when capabilities tab is rendered
        setTimeout(() => {
            const searchFilter = document.getElementById('search-filter');
            if (searchFilter) {
                searchFilter.addEventListener('input', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (typeof this.filterBySearch === 'function') {
                        this.filterBySearch(e.target.value);
                    }
                });
            } else {
                console.warn('⚠️ search-filter element not found');
            }
            
            const clearSearchBtn = document.getElementById('clear-search');
            if (clearSearchBtn) {
                clearSearchBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (typeof this.clearSearch === 'function') {
                        this.clearSearch();
                    }
                });
            } else {
                console.warn('⚠️ clear-search element not found');
            }
            
            const typeFilter = document.getElementById('capability-type-filter');
            if (typeFilter) {
                typeFilter.addEventListener('change', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (typeof this.filterByType === 'function') {
                        this.filterByType(e.target.value);
                    }
                });
            } else {
                console.warn('⚠️ capability-type-filter element not found');
            }
            
            const domainFilter = document.getElementById('domain-filter');
            if (domainFilter) {
                domainFilter.addEventListener('change', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (typeof this.filterByDomain === 'function') {
                        this.filterByDomain(e.target.value);
                    }
                });
            } else {
                console.warn('⚠️ domain-filter element not found');
            }
            
            const sortFilter = document.getElementById('sort-filter');
            if (sortFilter) {
                sortFilter.addEventListener('change', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (typeof this.sortByOption === 'function') {
                        this.sortByOption(e.target.value);
                    }
                });
            } else {
                console.warn('⚠️ sort-filter element not found');
            }
        }, 200);

        // Persist local draft on unload/visibility changes
        window.addEventListener('beforeunload', () => {
            if (typeof this.persistDraft === 'function') {
                try { this.persistDraft(); } catch (e) { /* no-op */ }
            }
        });
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden' && typeof this.persistDraft === 'function') {
                try { this.persistDraft(); } catch (e) { /* no-op */ }
            }
        });
    }
}
