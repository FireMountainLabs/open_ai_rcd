/**
 * Data Manager Module
 * Handles all data loading and API communication
 */

class DataManager extends BaseModule {
    constructor() {
        super('DataManager');
        this.data = {
            risks: null,
            controls: null,
            questions: null,
            network: null,
            gaps: null
        };
    }

    /**
     * Load all data from the API
     * @returns {Promise<Object>} Complete dataset
     */
    async loadData() {
        return await this.safeAsync(async () => {
            this.showLoading('Loading data...');
            
            const [risks, controls, questions, network, gaps] = await Promise.all([
                this.fetchRisks(),
                this.fetchControls(),
                this.fetchQuestions(),
                this.fetchNetwork(),
                this.fetchGaps()
            ]);

            this.data = { risks, controls, questions, network, gaps };
            this.hideLoading();
            
            this.logger.info('Data loaded successfully');
            return this.data;
        }, 'Failed to load data');
    }

    /**
     * Fetch risks data
     * @returns {Promise<Object>} Risks data
     */
    async fetchRisks() {
        const response = await fetch('/api/risks');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    }

    /**
     * Fetch controls data
     * @returns {Promise<Object>} Controls data
     */
    async fetchControls() {
        const response = await fetch('/api/controls');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    }

    /**
     * Fetch questions data
     * @returns {Promise<Object>} Questions data
     */
    async fetchQuestions() {
        const response = await fetch('/api/questions');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    }

    /**
     * Fetch network data
     * @returns {Promise<Object>} Network data
     */
    async fetchNetwork() {
        const response = await fetch('/api/network');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    }

    /**
     * Fetch gaps data
     * @returns {Promise<Object>} Gaps data
     */
    async fetchGaps() {
        const response = await fetch('/api/gaps');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    }

    /**
     * Search entities
     * @param {string} query - Search query
     * @returns {Promise<Array>} Search results
     */
    async searchEntities(query) {
        if (!query.trim()) {
            return [];
        }

        return await this.safeAsync(async () => {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            return data.results || [];
        }, 'Search failed');
    }

    /**
     * Get detailed entity information
     * @param {string} type - Entity type (risk, control, question)
     * @param {string} id - Entity ID
     * @returns {Promise<Object>} Detailed entity data
     */
    async getEntityDetail(type, id) {
        return await this.safeAsync(async () => {
            const response = await fetch(`/api/${type}/${id}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        }, `Failed to load ${type} details`);
    }

    /**
     * Get last updated times
     * @returns {Promise<Object>} Last updated information
     */
    async getLastUpdated() {
        return await this.safeAsync(async () => {
            const response = await fetch('/api/last-updated');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        }, 'Failed to load last updated times');
    }
}
