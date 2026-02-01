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
