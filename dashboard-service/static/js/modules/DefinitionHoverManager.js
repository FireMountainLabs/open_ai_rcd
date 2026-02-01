/**
 * Definition Hover Manager
 * 
 * Handles definition tooltips and navigation for terms in risks, controls, and questions.
 * Provides hover cards with definition information and click-to-navigate functionality.
 * 
 * @class DefinitionHoverManager
 * @example
 * const hoverManager = new DefinitionHoverManager(dashboard);
 * hoverManager.updateDefinitions(definitions);
 * hoverManager.enhanceContent(document.body);
 */

class DefinitionHoverManager {
    constructor(dashboard) {
        this.dashboard = dashboard;
        this.definitions = new Map();
        this.hoverCard = null;
        this.currentHoveredTerm = null;
        this.hoverTimeout = null;
        
        // Configuration
        this.config = {
            enabledTabs: ['risks', 'controls', 'questions', 'modal'],
            disabledTabs: ['definitions'],
            hoverDelay: 300,
            cardMaxWidth: 350,
            descriptionMaxLength: 100
        };
        
        this.init();
    }

    init() {
        this.createHoverCard();
        this.setupEventListeners();
    }

    /**
     * Build definition lookup map from definitions data
     * 
     * Creates a Map with multiple normalized variations of each term for flexible matching.
     * Stores terms in lowercase, normalized (no punctuation), and dash-variation formats.
     * 
     * @param {Array<Object>} definitions - Array of definition objects
     * @param {string} definitions[].term - The definition term
     * @param {string} definitions[].title - The definition title
     * @param {string} definitions[].description - The definition description
     * @param {string} definitions[].category - The definition category
     * @param {string} definitions[].source - The definition source
     * @returns {void}
     * 
     * @example
     * const definitions = [
     *   { term: "AI Agent", title: "AI Agent", description: "An autonomous software entity..." }
     * ];
     * hoverManager.buildDefinitionMap(definitions);
     */
    buildDefinitionMap(definitions) {
        this.definitions.clear();
        
        if (!definitions || !Array.isArray(definitions)) {
            return;
        }

        definitions.forEach(def => {
            if (def.term && def.term.trim()) {
                const definitionData = {
                    term: def.term,
                    title: def.title || '',
                    description: def.description || '',
                    category: def.category || '',
                    source: def.source || '',
                    definition_id: def.definition_id || '',
                    definitionId: def.definition_id || ''
                };
                
                // Store by lowercase term for case-insensitive matching
                const key = def.term.toLowerCase();
                this.definitions.set(key, definitionData);
                
                // Also store normalized versions for flexible matching
                const normalizedTerm = def.term.toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim();
                if (normalizedTerm !== key) {
                    this.definitions.set(normalizedTerm, definitionData);
                }
                
                // Store dash variation (replace dashes with spaces)
                const dashVariation = def.term.toLowerCase().replace(/-/g, ' ').replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim();
                if (dashVariation !== key && dashVariation !== normalizedTerm) {
                    this.definitions.set(dashVariation, definitionData);
                }
                
            }
        });
    }

    /**
     * Check if hover functionality is enabled for current tab
     * 
     * @param {string} tabName - The name of the tab to check
     * @returns {boolean} True if hover is enabled for this tab
     * 
     * @example
     * if (hoverManager.isEnabledForTab('risks')) {
     *   // Enable hover functionality
     * }
     */
    isEnabledForTab(tabName) {
        return this.config.enabledTabs.includes(tabName) && 
               !this.config.disabledTabs.includes(tabName);
    }

    /**
     * Check if the container is inside a definition modal
     * 
     * @param {HTMLElement} container - The container to check
     * @returns {boolean} True if inside a definition modal
     */
    isInsideDefinitionModal(container) {
        // Check if container or any parent has a class indicating it's a definition modal
        let element = container;
        while (element && element !== document.body) {
            // Check for modal body specifically
            if (element.id === 'modalBody') {
                // Check if this modal contains definition-specific content
                const hasDefinitionContent = element.querySelector('.detail-label') && 
                                           element.textContent.includes('Definition:');
                if (hasDefinitionContent) {
                    return true;
                }
            }
            
            // Check for modal classes
            if (element.classList && (
                element.classList.contains('definition-modal') ||
                element.classList.contains('definition-detail-modal') ||
                element.classList.contains('modal-content')
            )) {
                // Additional check: see if this is specifically a definition modal
                const modalBody = element.querySelector('#modalBody');
                if (modalBody) {
                    const hasDefinitionContent = modalBody.querySelector('.detail-label') && 
                                               modalBody.textContent.includes('Definition:');
                    if (hasDefinitionContent) {
                        return true;
                    }
                }
            }
            element = element.parentElement;
        }
        return false;
    }

    /**
     * Enhance content with definition hover functionality
     * 
     * Processes all text nodes in the container and wraps defined terms with hover spans.
     * Only processes content if hover is enabled for the specified tab.
     * 
     * @param {HTMLElement} container - The DOM container to enhance
     * @param {string} tabName - The name of the current tab
     * @returns {void}
     * 
     * @example
     * hoverManager.enhanceContent(document.getElementById('risksTable'), 'risks');
     */
    enhanceContent(container, tabName) {
        // Skip if we're inside a definition modal to avoid recursive linking
        if (this.isInsideDefinitionModal(container)) {
            return;
        }
        
        if (!this.isEnabledForTab(tabName)) {
            return;
        }

        if (this.definitions.size === 0) {
            return;
        }

        // Find all text content that might contain defined terms
        const textNodes = this.getTextNodes(container);
        
        textNodes.forEach(node => {
            if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
                this.processTextNode(node);
            }
        });
    }

    /**
     * Get all text nodes within a container
     */
    getTextNodes(container) {
        const textNodes = [];
        const walker = document.createTreeWalker(
            container,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    // Skip nodes that are already inside definition spans
                    if (node.parentElement && node.parentElement.classList.contains('has-definition')) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );

        let node;
        while (node = walker.nextNode()) {
            textNodes.push(node);
        }

        return textNodes;
    }

    /**
     * Process a text node and wrap defined terms
     */
    processTextNode(textNode) {
        const text = textNode.textContent;
        if (!text || text.length < 2) return;

        // Create regex pattern for all defined terms with word boundaries
        const terms = Array.from(this.definitions.keys());
        if (terms.length === 0) return;

        // Escape special regex characters and create word boundary pattern
        const escapedTerms = terms.map(term => 
            term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        );
        const pattern = new RegExp(`\\b(${escapedTerms.join('|')})\\b`, 'gi');

        const matches = [...text.matchAll(pattern)];
        
        if (matches.length === 0) {
            // Fallback: try case-insensitive substring matching for terms with hyphens
            const fallbackMatches = this.findFallbackMatches(text, terms);
            if (fallbackMatches.length === 0) {
                return;
            }
            this.processFallbackMatches(textNode, fallbackMatches);
            return;
        }

        // Create document fragment with wrapped terms
        const fragment = document.createDocumentFragment();
        let lastIndex = 0;

        matches.forEach(match => {
            const matchedTerm = match[0];
            const matchIndex = match.index;
            
            // Add text before the match
            if (matchIndex > lastIndex) {
                fragment.appendChild(document.createTextNode(text.slice(lastIndex, matchIndex)));
            }

            // Create wrapped term
            const span = document.createElement('span');
            span.className = 'has-definition';
            span.setAttribute('data-term', matchedTerm);
            span.textContent = matchedTerm;
            
            fragment.appendChild(span);
            lastIndex = matchIndex + matchedTerm.length;
        });

        // Add remaining text
        if (lastIndex < text.length) {
            fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
        }

        // Replace the text node
        textNode.parentNode.replaceChild(fragment, textNode);
    }

    /**
     * Create the hover card element
     */
    createHoverCard() {
        this.hoverCard = document.createElement('div');
        this.hoverCard.className = 'definition-hover-card';
        this.hoverCard.style.display = 'none';
        document.body.appendChild(this.hoverCard);

        // Add click listener to the hover card (only once)
        this.hoverCard.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (this.currentHoveredTerm) {
                // Store the term before hiding the card
                const termToNavigate = this.currentHoveredTerm;
                this.hideCard();
                this.showDefinitionModal(termToNavigate);
            }
        });
    }

    /**
     * Setup event listeners for hover functionality
     */
    setupEventListeners() {
        // Use event delegation for hover events
        document.addEventListener('mouseover', (e) => {
            if (e.target.classList.contains('has-definition')) {
                this.handleMouseOver(e);
            }
        });

        document.addEventListener('mouseout', (e) => {
            if (e.target.classList.contains('has-definition')) {
                this.handleMouseOut(e);
            }
        });

        // Remove click handler from definition terms - only hover cards are clickable

        // Hide card when clicking elsewhere
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.definition-hover-card') && 
                !e.target.classList.contains('has-definition')) {
                this.hideCard();
            }
        });
    }

    /**
     * Handle mouse over event on definition terms
     */
    handleMouseOver(e) {
        const term = e.target.getAttribute('data-term');
        if (!term) return;

        // Clear any existing timeout
        if (this.hoverTimeout) {
            clearTimeout(this.hoverTimeout);
        }

        // Set timeout for hover delay
        this.hoverTimeout = setTimeout(() => {
            this.showCard(e.target, term);
        }, this.config.hoverDelay);
    }

    /**
     * Handle mouse out event on definition terms
     */
    handleMouseOut(e) {
        // Clear timeout if mouse leaves before delay
        if (this.hoverTimeout) {
            clearTimeout(this.hoverTimeout);
            this.hoverTimeout = null;
        }

        // Hide card after a longer delay to allow moving to it
        setTimeout(() => {
            if (!this.hoverCard.matches(':hover')) {
                this.hideCard();
            }
        }, 300);
    }


    /**
     * Show the hover card
     */
    showCard(element, term) {
        const definition = this.definitions.get(term.toLowerCase());
        if (!definition) {
            return;
        }

        this.currentHoveredTerm = term;

        // Populate card content
        this.hoverCard.innerHTML = `
            <div class="hover-card-header">
                <strong class="hover-card-term">${definition.term}</strong>
                ${definition.title ? `<div class="hover-card-title">${definition.title}</div>` : ''}
            </div>
            <div class="hover-card-content">
                <div class="hover-card-description">
                    ${this.truncateText(definition.description, this.config.descriptionMaxLength)}
                </div>
                ${definition.source ? `<div class="hover-card-source">Source: ${definition.source}</div>` : ''}
            </div>
            <div class="hover-card-footer">
                Click to view full definition
            </div>
        `;

        // Position the card
        this.positionCard(element);
        this.hoverCard.style.display = 'block';
        
        // Fade in smoothly after positioning
        setTimeout(() => {
            this.hoverCard.style.opacity = '1';
        }, 10);

        // Add hover listeners to the card itself
        this.hoverCard.addEventListener('mouseenter', () => {
            if (this.hoverTimeout) {
                clearTimeout(this.hoverTimeout);
            }
        });

        this.hoverCard.addEventListener('mouseleave', () => {
            this.hideCard();
        });
    }

    /**
     * Hide the hover card
     */
    hideCard() {
        this.hoverCard.style.display = 'none';
        this.currentHoveredTerm = null;
    }

    /**
     * Position the hover card centered in the viewport
     */
    positionCard(element) {
        const card = this.hoverCard;
        
        // Calculate z-index to be higher than any stacked modals
        const existingModals = document.querySelectorAll('.modal');
        const modalCount = existingModals.length;
        const baseZIndex = 2000;
        const maxModalZIndex = baseZIndex + modalCount;
        const hoverCardZIndex = maxModalZIndex + 1;
        
        // Ensure the card is positioned correctly before showing
        card.style.position = 'fixed';
        card.style.left = '50%';
        card.style.top = '50%';
        card.style.transform = 'translate(-50%, -50%)';
        card.style.zIndex = hoverCardZIndex.toString();
        card.style.opacity = '0';
    }

    /**
     * Show definition modal for the given term
     */
    showDefinitionModal(term) {
        if (!this.dashboard || typeof this.dashboard.showDetailModal !== 'function') {
            return;
        }

        // Find the definition data for this term
        const definition = this.definitions.get(term.toLowerCase());
        if (!definition) {
            return;
        }

        this.dashboard.showDetailModal('definition', definition);
    }

    /**
     * Truncate text to specified length
     */
    truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    /**
     * Update definitions data
     */
    updateDefinitions(definitions) {
        this.buildDefinitionMap(definitions);
    }

    /**
     * Find fallback matches using case-insensitive substring matching
     */
    findFallbackMatches(text, terms) {
        const matches = [];
        const lowerText = text.toLowerCase();
        
        terms.forEach(term => {
            const lowerTerm = term.toLowerCase();
            let index = 0;
            
            while ((index = lowerText.indexOf(lowerTerm, index)) !== -1) {
                // Check if it's a word boundary (not part of another word)
                const before = index > 0 ? lowerText[index - 1] : ' ';
                const after = index + lowerTerm.length < lowerText.length ? lowerText[index + lowerTerm.length] : ' ';
                
                if (!/\w/.test(before) && !/\w/.test(after)) {
                    matches.push({
                        term: term,
                        originalText: text.substring(index, index + lowerTerm.length),
                        index: index,
                        length: lowerTerm.length
                    });
                }
                index += lowerTerm.length;
            }
        });
        
        return matches;
    }

    /**
     * Process fallback matches and wrap them
     */
    processFallbackMatches(textNode, matches) {
        if (matches.length === 0) return;
        
        // Sort matches by index (descending) to avoid index shifting
        matches.sort((a, b) => b.index - a.index);
        
        const text = textNode.textContent;
        const fragment = document.createDocumentFragment();
        let lastIndex = text.length;
        
        matches.forEach(match => {
            // Add text after the match
            if (match.index + match.length < lastIndex) {
                fragment.insertBefore(
                    document.createTextNode(text.substring(match.index + match.length, lastIndex)),
                    fragment.firstChild
                );
            }
            
            // Create wrapped term
            const span = document.createElement('span');
            span.className = 'has-definition';
            span.setAttribute('data-term', match.term);
            span.textContent = match.originalText;
            fragment.insertBefore(span, fragment.firstChild);
            
            lastIndex = match.index;
        });
        
        // Add remaining text before first match
        if (lastIndex > 0) {
            fragment.insertBefore(
                document.createTextNode(text.substring(0, lastIndex)),
                fragment.firstChild
            );
        }
        
        // Replace the text node with the fragment
        textNode.parentNode.replaceChild(fragment, textNode);
    }

    /**
     * Clean up resources
     */
    destroy() {
        if (this.hoverCard && this.hoverCard.parentNode) {
            this.hoverCard.parentNode.removeChild(this.hoverCard);
        }
        
        if (this.hoverTimeout) {
            clearTimeout(this.hoverTimeout);
        }
    }
}
