class DashboardSearch extends DashboardScenarios {
    async performSearch(query) {
        if (!query.trim()) {
            document.getElementById('searchResults').style.display = 'none';
            return;
        }

        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            this.displaySearchResults(data.results);
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    displaySearchResults(results) {
        const container = document.getElementById('searchResults');
        
        if (results.length === 0) {
            container.innerHTML = '<div class="search-result-item">No results found</div>';
        } else {
            container.innerHTML = results.map(result => {
                const typeLabel = this.formatTypeLabel(result.type);
                return `
                    <div class="search-result-item" onclick="dashboard.showDetailModal('${result.type}', ${JSON.stringify(result).replace(/"/g, '&quot;')})">
                        <span class="search-result-type">${typeLabel}</span>
                        <span class="search-result-title">${result.title}</span>
                        <div class="search-result-description">${result.description}</div>
                    </div>
                `;
            }).join('');
        }
        
        container.style.display = 'block';
    }

    formatTypeLabel(type) {
        const typeLabels = {
            'risk': 'RISK',
            'control': 'CONTROL', 
            'question': 'QUESTION',
            'definition': 'DEFINITION'
        };
        return typeLabels[type] || type.toUpperCase();
    }
}
