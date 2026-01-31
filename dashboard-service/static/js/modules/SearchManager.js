/**
 * Search Manager Module
 * Handles search functionality and results display
 */

class SearchManager extends BaseModule {
    constructor(dataManager) {
        super('SearchManager');
        this.dataManager = dataManager;
        this.searchTimeout = null;
        this.debounceDelay = this.getConfig('search.debounceDelay', 300);
    }

    /**
     * Initialize search functionality
     */
    init() {
        this.setupSearchInput();
        this.setupSearchResults();
    }

    /**
     * Setup search input event listeners
     */
    setupSearchInput() {
        const searchInput = document.getElementById('searchInput');
        if (!searchInput) return;

        searchInput.addEventListener('input', (e) => {
            this.handleSearchInput(e.target.value);
        });

        // Close search results when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                this.hideSearchResults();
            }
        });
    }

    /**
     * Setup search results container
     */
    setupSearchResults() {
        const searchResults = document.getElementById('searchResults');
        if (!searchResults) return;

        // Ensure search results container exists
        if (!searchResults.parentNode) {
            const searchContainer = document.querySelector('.search-container');
            if (searchContainer) {
                searchContainer.appendChild(searchResults);
            }
        }
    }

    /**
     * Handle search input with debouncing
     * @param {string} query - Search query
     */
    handleSearchInput(query) {
        clearTimeout(this.searchTimeout);
        
        if (!query.trim()) {
            this.hideSearchResults();
            return;
        }

        this.searchTimeout = setTimeout(() => {
            this.performSearch(query);
        }, this.debounceDelay);
    }

    /**
     * Perform search operation
     * @param {string} query - Search query
     */
    async performSearch(query) {
        try {
            this.showSearchLoading();
            const results = await this.dataManager.searchEntities(query);
            this.displaySearchResults(results);
        } catch (error) {
            this.logger.error('Search error:', error);
            this.showSearchError('Search failed. Please try again.');
        }
    }

    /**
     * Show search loading state
     */
    showSearchLoading() {
        const searchResults = document.getElementById('searchResults');
        if (!searchResults) return;

        searchResults.innerHTML = '<div class="search-result-item loading">Searching...</div>';
        searchResults.style.display = 'block';
    }

    /**
     * Show search error
     * @param {string} message - Error message
     */
    showSearchError(message) {
        const searchResults = document.getElementById('searchResults');
        if (!searchResults) return;

        searchResults.innerHTML = `<div class="search-result-item error">${message}</div>`;
        searchResults.style.display = 'block';
    }

    /**
     * Display search results
     * @param {Array} results - Search results
     */
    displaySearchResults(results) {
        const searchResults = document.getElementById('searchResults');
        if (!searchResults) return;

        if (results.length === 0) {
            searchResults.innerHTML = '<div class="search-result-item">No results found</div>';
        } else {
            searchResults.innerHTML = results.map(result => this.createSearchResultItem(result)).join('');
        }
        
        searchResults.style.display = 'block';
    }

    /**
     * Create search result item HTML
     * @param {Object} result - Search result object
     * @returns {string} HTML string
     */
    createSearchResultItem(result) {
        const typeClass = `search-result-type-${result.type}`;
        const safeData = this.escapeHtml(JSON.stringify(result));
        
        return `
            <div class="search-result-item" 
                 onclick="window.dashboard.showDetailModal('${result.type}', ${safeData})">
                <span class="search-result-type ${typeClass}">${result.type}</span>
                <span class="search-result-title">${this.escapeHtml(result.title)}</span>
                <div class="search-result-description">${this.escapeHtml(result.description)}</div>
            </div>
        `;
    }

    /**
     * Hide search results
     */
    hideSearchResults() {
        const searchResults = document.getElementById('searchResults');
        if (searchResults) {
            searchResults.style.display = 'none';
        }
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Clear search input
     */
    clearSearch() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = '';
            this.hideSearchResults();
        }
    }

    /**
     * Set debounce delay
     * @param {number} delay - Delay in milliseconds
     */
    setDebounceDelay(delay) {
        this.debounceDelay = delay;
    }
}
