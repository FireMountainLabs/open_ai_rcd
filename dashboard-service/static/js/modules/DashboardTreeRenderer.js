class DashboardTreeRenderer extends DashboardCore {
    createVerticalTree() {
        if (!this.treeData || this.treeData.length === 0) {
            this.showError('No capability data available');
            return;
        }
        
        // Ensure capabilitiesWithUniqueControls is initialized
        if (!this.capabilitiesWithUniqueControls) {
            this.capabilitiesWithUniqueControls = new Set();
        }
        // Ensure uniqueControlIds is initialized
        if (!this.uniqueControlIds) {
            this.uniqueControlIds = {};
        }
        
        // Clear existing content
        this.treeGroup.selectAll('*').remove();
        
        // Get actual container width
        const containerElement = document.getElementById('tree-visualization');
        const containerWidth = containerElement ? containerElement.clientWidth - 100 : this.width - 100;
        // Filter capabilities by type, domain, and search term
        let filteredCapabilities = this.treeData;
        if (this.selectedType) {
            filteredCapabilities = filteredCapabilities.filter(cap => cap.capability_type === this.selectedType);
        }
        if (this.selectedDomain) {
            filteredCapabilities = filteredCapabilities.filter(cap => cap.capability_domain === this.selectedDomain);
        }
        if (this.searchTerm) {
            filteredCapabilities = filteredCapabilities.filter(cap => 
                cap.capability_name.toLowerCase().includes(this.searchTerm) ||
                (cap.capability_description && cap.capability_description.toLowerCase().includes(this.searchTerm))
            );
        }
        
        // Sort capabilities based on selected sort option
        const capabilitiesToShow = this.sortCapabilitiesByType(filteredCapabilities);
        
        if (capabilitiesToShow.length === 0) {
            this.treeGroup.append('text')
                .attr('x', containerWidth / 2)
                .attr('y', this.height / 2)
                .attr('text-anchor', 'middle')
                .text('No capabilities found')
                .style('font-size', '16px')
                .style('fill', '#666');
            return;
        }
        
        // Calculate grid layout for exactly 4 columns
        const maxColumns = 4;
        const padding = 40; // Total horizontal padding
        const availableWidth = containerWidth - padding;
        const capabilityWidth = Math.floor(availableWidth / maxColumns) - 10; // 10px margin between items
        // Increased base height to accommodate longer names
        const capabilityHeight = 140; // Increased from 120 to allow more text
        const rowHeight = capabilityHeight + 20; // Increased spacing for better readability
        const columnWidth = Math.floor(availableWidth / maxColumns);
        
        // Determine if we should show section headers
        const shouldShowHeaders = !this.selectedType && (this.sortBy === 'type-name' || this.sortBy === 'active');
        
        if (shouldShowHeaders) {
            let currentIndex = 0;
            
            if (this.sortBy === 'type-name') {
                // Group capabilities by type for visual separation
                const technicalCapabilities = capabilitiesToShow.filter(cap => cap.capability_type === 'technical');
                const nonTechnicalCapabilities = capabilitiesToShow.filter(cap => cap.capability_type === 'non-technical');
                
                // Add technical capabilities first
                if (technicalCapabilities.length > 0) {
                    const headerY = 15;
                    const cardsStartY = headerY + 20; // Cards start 20px below header
                    
                    // Add section header for technical capabilities
                    this.treeGroup.append('text')
                        .attr('x', 20)
                        .attr('y', headerY)
                        .text('Technical Capabilities')
                        .style('font-size', '16px')
                        .style('font-weight', 'bold')
                        .style('fill', '#2c3e50');
                    
                    technicalCapabilities.forEach((capability) => {
                        const row = Math.floor(currentIndex / maxColumns);
                        const col = currentIndex % maxColumns;
                        const xOffset = col * columnWidth + 20;
                        const yOffset = row * rowHeight + cardsStartY;
                        
                        this.createCapabilityColumn(capability, xOffset, yOffset, capabilityWidth - 20);
                        currentIndex++;
                    });
                }
                
                // Add non-technical capabilities after technical ones
                if (nonTechnicalCapabilities.length > 0) {
                    // Add section header for non-technical capabilities
                    const technicalRows = Math.ceil(technicalCapabilities.length / maxColumns);
                    const headerY = technicalRows * rowHeight + 45;
                    
                    this.treeGroup.append('text')
                        .attr('x', 20)
                        .attr('y', headerY)
                        .text('Non-Technical Capabilities')
                        .style('font-size', '16px')
                        .style('font-weight', 'bold')
                        .style('fill', '#2c3e50');
                    
                    // Reset currentIndex for non-technical capabilities
                    let nonTechIndex = 0;
                    nonTechnicalCapabilities.forEach((capability) => {
                        const row = Math.floor(nonTechIndex / maxColumns);
                        const col = nonTechIndex % maxColumns;
                        const xOffset = col * columnWidth + 20;
                        const yOffset = row * rowHeight + headerY + 25; // Start below header
                        
                        this.createCapabilityColumn(capability, xOffset, yOffset, capabilityWidth - 20);
                        nonTechIndex++;
                    });
                }
            } else if (this.sortBy === 'active') {
                // Group capabilities by active/disabled status
                const activeCapabilities = capabilitiesToShow.filter(cap => this.activeCapabilities.has(cap.capability_id));
                const inactiveCapabilities = capabilitiesToShow.filter(cap => !this.activeCapabilities.has(cap.capability_id));
                
                // Add active capabilities first
                if (activeCapabilities.length > 0) {
                    // Add section header for active capabilities
                    this.treeGroup.append('text')
                        .attr('x', 20)
                        .attr('y', 15)
                        .text('Active Capabilities')
                        .style('font-size', '16px')
                        .style('font-weight', 'bold')
                        .style('fill', '#27ae60');
                    
                    activeCapabilities.forEach((capability) => {
                        const row = Math.floor(currentIndex / maxColumns);
                        const col = currentIndex % maxColumns;
                        const xOffset = col * columnWidth + 20;
                        const yOffset = row * rowHeight + 40; // Start below header
                        
                        this.createCapabilityColumn(capability, xOffset, yOffset, capabilityWidth - 20);
                        currentIndex++;
                    });
                }
                
                // Add inactive capabilities after active ones
                if (inactiveCapabilities.length > 0) {
                    // Add section header for inactive capabilities
                    const activeRows = Math.ceil(activeCapabilities.length / maxColumns);
                    const headerY = activeRows * rowHeight + 60;
                    
                    this.treeGroup.append('text')
                        .attr('x', 20)
                        .attr('y', headerY)
                        .text('Inactive Capabilities')
                        .style('font-size', '16px')
                        .style('font-weight', 'bold')
                        .style('fill', '#e74c3c');
                    
                    inactiveCapabilities.forEach((capability) => {
                        const row = Math.floor(currentIndex / maxColumns);
                        const col = currentIndex % maxColumns;
                        const xOffset = col * columnWidth + 20;
                        const yOffset = row * rowHeight + headerY + 25; // Start below header
                        
                        this.createCapabilityColumn(capability, xOffset, yOffset, capabilityWidth - 20);
                        currentIndex++;
                    });
                }
            }
        } else {
            // Show all capabilities in a single grid without section headers
            capabilitiesToShow.forEach((capability, index) => {
                const row = Math.floor(index / maxColumns);
                const col = index % maxColumns;
                const xOffset = col * columnWidth + 20;
                const yOffset = row * rowHeight + 20;
                
                this.createCapabilityColumn(capability, xOffset, yOffset, capabilityWidth - 20);
            });
        }
        
        // Update SVG height based on content
        let totalHeight = 20; // Base padding
        
        if (shouldShowHeaders) {
            // All capabilities view with headers
            if (this.sortBy === 'type-name') {
                const technicalCapabilities = capabilitiesToShow.filter(cap => cap.capability_type === 'technical');
                const nonTechnicalCapabilities = capabilitiesToShow.filter(cap => cap.capability_type === 'non-technical');
                const technicalRows = Math.ceil(technicalCapabilities.length / maxColumns);
                const nonTechnicalRows = Math.ceil(nonTechnicalCapabilities.length / maxColumns);
                
                if (technicalCapabilities.length > 0) {
                    totalHeight += 30; // Technical header
                    totalHeight += technicalRows * rowHeight;
                }
                if (nonTechnicalCapabilities.length > 0) {
                    totalHeight += 30; // Non-technical header
                    totalHeight += nonTechnicalRows * rowHeight;
                }
            } else if (this.sortBy === 'active') {
                const activeCapabilities = capabilitiesToShow.filter(cap => this.activeCapabilities.has(cap.capability_id));
                const inactiveCapabilities = capabilitiesToShow.filter(cap => !this.activeCapabilities.has(cap.capability_id));
                const activeRows = Math.ceil(activeCapabilities.length / maxColumns);
                const inactiveRows = Math.ceil(inactiveCapabilities.length / maxColumns);
                
                if (activeCapabilities.length > 0) {
                    totalHeight += 30; // Active header
                    totalHeight += activeRows * rowHeight;
                }
                if (inactiveCapabilities.length > 0) {
                    totalHeight += 30; // Inactive header
                    totalHeight += inactiveRows * rowHeight;
                }
            }
        } else {
            // Single grid view without headers
            const totalRows = Math.ceil(capabilitiesToShow.length / maxColumns);
            totalHeight += totalRows * rowHeight;
        }
        
        const newHeight = Math.max(800, totalHeight + 40);
        this.svg.attr('height', newHeight);
        
        // Also update the tree visualization container height
        const treeContainer = document.getElementById('tree-visualization');
        if (treeContainer) {
            treeContainer.style.height = `${newHeight}px`;
        }
    }

    createCapabilityColumn(capability, x, y, width) {
        const isActive = this.activeCapabilities.has(capability.capability_id);
        const controls = capability.controls || [];
        const risks = capability.risks || [];
        
        // Determine if capability is fully active or partially active
        let isFullyActive = false;
        let isPartiallyActive = false;
        let activeControlsCount = 0;
        
        if (isActive && controls.length > 0) {
            // Ensure activeControls is initialized
            if (!this.activeControls) {
                this.activeControls = new Set();
            }
            
            activeControlsCount = controls.filter(c => this.activeControls.has(c.control_id)).length;
            
            if (activeControlsCount === controls.length) {
                isFullyActive = true;
            } else {
                // Partially active: some controls active, or none active, or no controls exist
                isPartiallyActive = true;
            }
        } else if (isActive && controls.length === 0) {
            // Active but no controls - treat as partial (incomplete state)
            isPartiallyActive = true;
        }
        
        // Create tooltip text based on state
        let tooltipText = '';
        if (!isActive) {
            tooltipText = `Inactive: ${capability.capability_name}. Click to activate.`;
        } else if (isFullyActive) {
            tooltipText = `Fully Active: ${capability.capability_name}. All ${controls.length} controls are enabled.`;
        } else if (isPartiallyActive) {
            tooltipText = `Partially Active: ${capability.capability_name}. ${activeControlsCount} of ${controls.length} controls are enabled.`;
        } else {
            tooltipText = `Active: ${capability.capability_name}. Capability enabled but no controls active.`;
        }
        
        const capGroup = this.treeGroup.append('g')
            .attr('class', `capability-box ${isActive ? (isFullyActive ? 'fully-active' : isPartiallyActive ? 'partially-active' : 'active') : 'inactive'}`)
            .attr('transform', `translate(${x}, ${y})`)
            .attr('data-capability-id', capability.capability_id)
            .attr('title', tooltipText);
        
        const cardPadding = 16;
        
        // Determine stroke color and width based on state
        let strokeColor, strokeWidth, cardFill, filterEffect;
        
        if (!isActive) {
            strokeColor = '#d1d5db';
            strokeWidth = 1;
            cardFill = '#ffffff';
            filterEffect = 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.05))';
        } else if (isFullyActive) {
            strokeColor = '#10b981'; // Green for fully active
            strokeWidth = 3; // Thicker border for fully active
            cardFill = '#f0fdf4'; // Light green background
            filterEffect = 'drop-shadow(0 2px 8px rgba(16, 185, 129, 0.3))';
        } else if (isPartiallyActive) {
            strokeColor = '#f59e0b'; // Amber/orange for partially active
            strokeWidth = 2; // Medium border for partial
            cardFill = '#fffbeb'; // Light amber background
            filterEffect = 'drop-shadow(0 2px 6px rgba(245, 158, 11, 0.25))';
        }
        
        // Wrap the capability name first to determine how much space we need
        const titleY = 20;
        const nameLines = this.wrapText(capability.capability_name, width - (cardPadding * 2) - 60, 12); // Reserve space for badge
        
        // Calculate dynamic card height based on content
        const nameHeight = Math.max(nameLines.length * 14, 14); // At least one line
        const metricsHeight = 32; // Height for metrics row
        const minCardHeight = 100;
        const cardHeight = Math.max(minCardHeight, nameHeight + metricsHeight + 40); // Add padding
        
        const cardRect = capGroup.append('rect')
            .attr('width', width)
            .attr('height', cardHeight)
            .attr('rx', 6)
            .style('fill', cardFill)
            .style('stroke', strokeColor)
            .style('stroke-width', strokeWidth)
            .style('filter', filterEffect);

        // Render capability name lines
        nameLines.forEach((line, index) => {
            capGroup.append('text')
                .attr('x', cardPadding)
                .attr('y', titleY + (index * 14))
                .text(line)
                .style('fill', isActive ? '#111827' : '#9ca3af')
                .style('font-weight', '500')
                .style('font-size', '12px')
                .style('font-family', '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif');
        });
        
        // Position metrics below the name with appropriate spacing
        const metricsY = titleY + nameHeight + 16;
        
        // Improved metrics layout: 3-column grid with even spacing
        const metricsStartY = metricsY;
        const metricRowHeight = 32; // Height for each metric row
        const uniqueControlsCount = (this.uniqueControlCounts && this.uniqueControlCounts[capability.capability_id]) || 0;
        
        // Calculate column positions for balanced 3-column layout
        const metricsAvailableWidth = width - (cardPadding * 2) - 60; // Reserve space for badge
        const metricColumnWidth = metricsAvailableWidth / 3;
        const metric1X = cardPadding;
        const metric2X = cardPadding + metricColumnWidth;
        const metric3X = cardPadding + (metricColumnWidth * 2);
        
        // Controls metric (left column)
        const controlsDisplay = controls.length > 0 ? `${isActive ? activeControlsCount : 0}/${controls.length}` : '0';
        const controlsColor = !isActive ? '#9ca3af' : isFullyActive ? '#10b981' : isPartiallyActive ? '#f59e0b' : '#111827';
        
        capGroup.append('text')
            .attr('x', metric1X)
            .attr('y', metricsStartY)
            .text(controlsDisplay)
            .style('fill', controlsColor)
            .style('font-weight', '600')
            .style('font-size', '16px');
        
        capGroup.append('text')
            .attr('x', metric1X)
            .attr('y', metricsStartY + 14)
            .text('controls')
            .style('fill', '#9ca3af')
            .style('font-size', '10px')
            .style('font-weight', '400');
        
        // Risks metric (middle column)
        // Note: This shows risks that have controls in this capability
        // When activated, some may be fully covered, others partially covered
        const risksText = capGroup.append('text')
            .attr('x', metric2X)
            .attr('y', metricsStartY)
            .text(`${risks.length}`)
            .style('fill', isActive ? '#111827' : '#9ca3af')
            .style('font-weight', '600')
            .style('font-size', '16px');
        
        const risksLabel = capGroup.append('text')
            .attr('x', metric2X)
            .attr('y', metricsStartY + 14)
            .text('risks')
            .style('fill', '#9ca3af')
            .style('font-size', '10px')
            .style('font-weight', '400');
        
        // Add tooltip to explain the risks count
        const risksTooltip = isActive 
            ? `Risks with controls in this capability. When activated, some may be fully covered (all controls active) while others may be partially covered (need controls from other capabilities).`
            : `Risks that have controls mapped to this capability. Activate to see coverage status.`;
        
        risksText.append('title').text(risksTooltip);
        risksLabel.append('title').text(risksTooltip);
        
        // Unique controls metric (right column) - always show column, even if 0
        const uniqueDisplay = uniqueControlsCount > 0 ? `${uniqueControlsCount}` : '0';
        const uniqueColor = isActive ? '#111827' : '#9ca3af';
        
        capGroup.append('text')
            .attr('x', metric3X)
            .attr('y', metricsStartY)
            .text(uniqueDisplay)
            .style('fill', uniqueControlsCount > 0 ? uniqueColor : '#d1d5db') // Lighter gray if 0
            .style('font-weight', uniqueControlsCount > 0 ? '600' : '400')
            .style('font-size', '16px');
        
        capGroup.append('text')
            .attr('x', metric3X)
            .attr('y', metricsStartY + 14)
            .text('unique')
            .style('fill', '#9ca3af')
            .style('font-size', '10px')
            .style('font-weight', '400');
        
        // Unified text badge design for all states (top right)
        const badgeX = width - 54; // Position to accommodate 50px badge + 4px margin
        const badgeY = 4;
        const badgeWidth = 50;
        const badgeHeight = 16;
        
        // Determine badge text and color based on state
        let badgeText = '';
        let badgeColor = '';
        let letterSpacing = 0.3;
        
        if (isFullyActive) {
            badgeText = 'ACTIVE';
            badgeColor = '#10b981'; // Green
            letterSpacing = 0.5;
        } else if (isPartiallyActive) {
            badgeText = 'PARTIAL';
            badgeColor = '#f59e0b'; // Amber
            letterSpacing = 0.5;
        } else {
            badgeText = 'INACTIVE';
            badgeColor = '#9ca3af'; // Gray
            letterSpacing = 0.3;
        }
        
        // Create unified badge for all states
        const badgeGroup = capGroup.append('g')
            .attr('class', 'capability-status-badge')
            .style('cursor', 'pointer');
        
        // Badge background with shadow
        badgeGroup.append('rect')
            .attr('x', badgeX)
            .attr('y', badgeY)
            .attr('width', badgeWidth)
            .attr('height', badgeHeight)
            .attr('rx', 8)
            .style('fill', badgeColor)
            .style('opacity', 1.0)
            .style('filter', 'drop-shadow(0 1px 3px rgba(0, 0, 0, 0.2))');
        
        // Badge text - centered and properly aligned
        badgeGroup.append('text')
            .attr('x', badgeX + badgeWidth / 2)
            .attr('y', badgeY + 11)
            .text(badgeText)
            .style('fill', '#ffffff')
            .style('font-size', '8px')
            .style('font-weight', '700')
            .style('text-anchor', 'middle')
            .style('font-family', '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif')
            .style('letter-spacing', `${letterSpacing}px`)
            .style('pointer-events', 'none'); // Prevent text from blocking clicks
        
        // Make entire badge clickable for toggling
        badgeGroup.on('click', async (event) => {
            event.stopPropagation();
            event.preventDefault();
            await this.toggleCapability(capability);
        });
        
        capGroup
            .style('cursor', 'pointer')
            .on('mouseenter', () => {
                // Enhanced hover effect based on state
                if (isFullyActive) {
                    cardRect.transition().duration(100)
                        .style('filter', 'drop-shadow(0 4px 12px rgba(16, 185, 129, 0.4))')
                        .style('stroke-width', 4);
                } else if (isPartiallyActive) {
                    cardRect.transition().duration(100)
                        .style('filter', 'drop-shadow(0 4px 10px rgba(245, 158, 11, 0.35))')
                        .style('stroke-width', 3);
                } else {
                    cardRect.transition().duration(100)
                        .style('filter', 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1))');
                }
            })
            .on('mouseleave', () => {
                // Restore original filter and stroke
                cardRect.transition().duration(100)
                    .style('filter', filterEffect)
                    .style('stroke-width', strokeWidth);
            })
            .on('click', (event) => {
                // Don't open modal if clicking on the badge (it handles its own click)
                const clickedBadge = capGroup.select('.capability-status-badge').node();
                if (clickedBadge && (event.target === clickedBadge || clickedBadge.contains(event.target))) {
                    return;
                }
                this.showCapabilityModal(capability);
            });
    }

    truncateText(text, maxWidth) {
        const charLimit = Math.floor(maxWidth / 6);
        if (text.length <= charLimit) return text;
        return text.substring(0, charLimit - 3) + '...';
    }
    
    wrapText(text, maxWidth, fontSize) {
        // Calculate characters per line more accurately
        // Average character width is approximately fontSize * 0.6 for most fonts
        const charsPerLine = Math.floor(maxWidth / (fontSize * 0.6));
        const words = text.split(' ');
        const lines = [];
        let currentLine = '';
        
        for (const word of words) {
            const testLine = currentLine + (currentLine ? ' ' : '') + word;
            if (testLine.length <= charsPerLine) {
                currentLine = testLine;
            } else {
                if (currentLine) {
                    lines.push(currentLine);
                    currentLine = word;
                } else {
                    // Word is too long for one line - break it if needed
                    if (word.length > charsPerLine) {
                        // Try to break long words at reasonable points
                        let remaining = word;
                        while (remaining.length > charsPerLine) {
                            lines.push(remaining.substring(0, charsPerLine - 1) + '-');
                            remaining = remaining.substring(charsPerLine - 1);
                        }
                        currentLine = remaining;
                    } else {
                        currentLine = word;
                    }
                }
            }
        }
        
        if (currentLine) {
            lines.push(currentLine);
        }
        
        // Allow up to 4 lines for better readability
        // If still too long, show ellipsis on the last line
        const maxLines = 4;
        if (lines.length > maxLines) {
            const truncated = lines.slice(0, maxLines - 1);
            const lastLine = lines[maxLines - 1];
            // Truncate last line if it would be too long
            if (lastLine.length > charsPerLine - 3) {
                truncated.push(lastLine.substring(0, charsPerLine - 3) + '...');
            } else {
                truncated.push(lastLine + '...');
            }
            return truncated;
        }
        
        return lines;
    }
    
    setupSVG() {
        const container = document.getElementById('tree-visualization');
        if (!container) {
            console.error('Tree visualization container not found');
            return;
        }
        container.innerHTML = '';

        this.svg = d3.select(container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', this.height || 600)
            .style('border', '1px solid #ddd')
            .style('max-width', '100%');

        this.treeGroup = this.svg.append('g')
            .attr('transform', 'translate(40, 20)');
    }
    
    populateDomainFilter() {
        if (!this.treeData) return;
        
        const domainFilter = document.getElementById('domain-filter');
        if (!domainFilter) return;
        
        // Get unique domains from the data
        const domains = [...new Set(this.treeData
            .map(cap => cap.capability_domain)
            .filter(domain => domain && domain.trim() !== '')
        )].sort();
        
        // Clear existing options except "All Domains"
        domainFilter.innerHTML = '<option value="">All Domains</option>';
        
        // Add domain options
        domains.forEach(domain => {
            const option = document.createElement('option');
            option.value = domain;
            option.textContent = domain;
            domainFilter.appendChild(option);
        });
    }
    
    sortCapabilitiesByType(capabilities) {
        return [...capabilities].sort((a, b) => {
            switch (this.sortBy) {
                case 'name':
                    return a.capability_name.localeCompare(b.capability_name);
                
                case 'name-desc':
                    return b.capability_name.localeCompare(a.capability_name);
                
                case 'domain':
                    const domainA = a.capability_domain || '';
                    const domainB = b.capability_domain || '';
                    if (domainA !== domainB) {
                        return domainA.localeCompare(domainB);
                    }
                    return a.capability_name.localeCompare(b.capability_name);
                
                case 'controls':
                    const controlsA = a.controls ? a.controls.length : 0;
                    const controlsB = b.controls ? b.controls.length : 0;
                    if (controlsA !== controlsB) {
                        return controlsB - controlsA; // Descending order
                    }
                    return a.capability_name.localeCompare(b.capability_name);
                
                case 'risks':
                    const risksA = a.risks ? a.risks.length : 0;
                    const risksB = b.risks ? b.risks.length : 0;
                    if (risksA !== risksB) {
                        return risksB - risksA; // Descending order
                    }
                    return a.capability_name.localeCompare(b.capability_name);
                
                case 'unique':
                    const uniqueA = (this.uniqueControlCounts && this.uniqueControlCounts[a.capability_id]) || 0;
                    const uniqueB = (this.uniqueControlCounts && this.uniqueControlCounts[b.capability_id]) || 0;
                    if (uniqueA !== uniqueB) {
                        return uniqueB - uniqueA; // Descending order (most unique first)
                    }
                    return a.capability_name.localeCompare(b.capability_name);
                
                case 'active':
                    const activeA = this.activeCapabilities.has(a.capability_id);
                    const activeB = this.activeCapabilities.has(b.capability_id);
                    if (activeA !== activeB) {
                        return activeB - activeA; // Active first (true = 1, false = 0)
                    }
                    return a.capability_name.localeCompare(b.capability_name);
                
                case 'type-name':
                default:
                    // Default: technical first, then non-technical, then by name
                    if (a.capability_type === 'technical' && b.capability_type === 'non-technical') {
                        return -1; // technical comes first
                    }
                    if (a.capability_type === 'non-technical' && b.capability_type === 'technical') {
                        return 1; // non-technical comes after
                    }
                    // If same type, sort by name
                    return a.capability_name.localeCompare(b.capability_name);
            }
        });
    }
    
    showCapabilityModal(capability) {
        const modal = document.getElementById('detailModal');
        const modalBody = document.getElementById('modalBody');
        
        if (!modal || !modalBody) {
            console.error('Modal elements not found');
            return;
        }
        
        const isActive = this.activeCapabilities.has(capability.capability_id);
        
        const html = `
            <div class="capability-detail">
                <h2>${capability.capability_name}</h2>
                <div class="capability-meta">
                    <span class="badge">${capability.capability_type}</span>
                    <span class="badge">${capability.capability_domain || 'General'}</span>
                </div>
                
                ${capability.capability_definition ? `
                    <div class="description-section" style="margin: 1rem 0; padding: 1rem; background: #f9fafb; border-radius: 6px; border-left: 3px solid #6366f1;">
                        <p style="margin: 0; color: #374151; line-height: 1.6; font-size: 14px;">${capability.capability_definition}</p>
                    </div>
                ` : ''}
                
                <div class="toggle-section">
                    <label class="toggle-switch">
                        <input type="checkbox" 
                               id="capability-toggle-${capability.capability_id}" 
                               ${isActive ? 'checked' : ''}
                               data-capability-id="${capability.capability_id}">
                        <span class="toggle-slider"></span>
                    </label>
                    <span class="toggle-label">${isActive ? 'Enabled' : 'Disabled'}</span>
                </div>
                
                <div class="detail-section">
                    <h3 style="color: #00b0f0;">Controls Assigned (${capability.controls?.length || 0})</h3>
                    ${capability.controls?.length > 0 ? `
                        <div class="controls-list" style="display: flex; flex-direction: column; gap: 0.5rem;">
                            ${capability.controls.map(c => {
                                const isControlActive = this.isControlActive ? this.isControlActive(c.control_id) : (this.activeControls && this.activeControls.has(c.control_id));
                                const canToggle = isActive;
                                // Check if this control is unique for this capability
                                const isUnique = this.uniqueControlIds && 
                                                this.uniqueControlIds[capability.capability_id] && 
                                                this.uniqueControlIds[capability.capability_id].has(c.control_id);
                                return `
                                    <div class="control-item" style="display: flex; align-items: center; justify-content: space-between; padding: 0.75rem; border-left: 3px solid #00b0f0; background: #ffffff; border-radius: 4px;">
                                        <div style="flex: 1; display: flex; align-items: center; gap: 0.5rem;">
                                            ${isUnique ? '<span style="color: #ff6b00; font-size: 1.5rem; font-weight: bold; line-height: 1;">*</span>' : ''}
                                            <div>
                                                <strong>${c.control_id}:</strong> ${c.control_title}
                                            </div>
                                        </div>
                                        <label class="toggle-switch" style="margin-left: 1rem; ${!canToggle ? 'opacity: 0.5; cursor: not-allowed;' : ''}">
                                            <input type="checkbox" 
                                                   id="control-toggle-${c.control_id}" 
                                                   ${isControlActive ? 'checked' : ''}
                                                   ${!canToggle ? 'disabled' : ''}
                                                   data-control-id="${c.control_id}"
                                                   data-capability-id="${capability.capability_id}">
                                            <span class="toggle-slider"></span>
                                        </label>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    ` : `
                        <div class="no-controls-message">
                            <p><em>${capability.capability_type === 'non-technical' ? 
                                'Non-technical capabilities focus on governance, policies, and processes rather than direct technical controls.' : 
                                'No technical controls are currently mapped to this capability.'}</em></p>
                        </div>
                    `}
                </div>
                
                <div class="detail-section">
                    <h3 style="color: #ffbf00;">Risks Controlled (${capability.risks?.length || 0})</h3>
                    <ul>
                        ${(capability.risks || []).map(r => `
                            <li style="color: #000000; border-left: 3px solid #ffbf00; padding: 0.5rem 0 0.5rem 1rem; margin: 0.25rem 0; background: #ffffff; border-radius: 4px;"><strong>${r.risk_id}:</strong> ${r.risk_title}</li>
                        `).join('')}
                    </ul>
                </div>
            </div>
        `;
        
        modalBody.innerHTML = html;
        modal.style.display = 'block';
        
        // Add toggle event listener for capability
        const toggle = document.getElementById(`capability-toggle-${capability.capability_id}`);
        if (toggle) {
            toggle.addEventListener('change', async (e) => {
                await this.toggleCapability(capability);
                // Update label
                const label = toggle.closest('.toggle-section')?.querySelector('.toggle-label');
                if (label) {
                    label.textContent = e.target.checked ? 'Enabled' : 'Disabled';
                }
                // Refresh modal to update control toggles state
                this.showCapabilityModal(capability);
            });
        }
        
        // Add toggle event listeners for controls
        if (capability.controls && capability.controls.length > 0) {
            capability.controls.forEach(control => {
                const controlToggle = document.getElementById(`control-toggle-${control.control_id}`);
                if (controlToggle) {
                    controlToggle.addEventListener('change', async (e) => {
                        const controlId = e.target.dataset.controlId;
                        const capabilityId = e.target.dataset.capabilityId;
                        
                        // Ensure activeControls is initialized
                        if (!this.activeControls) {
                            this.activeControls = new Set();
                        }
                        
                        // Only allow toggling if the capability is active
                        if (!this.activeCapabilities.has(capabilityId)) {
                            console.warn(`Cannot toggle control ${controlId}: capability ${capabilityId} is not active`);
                            e.target.checked = !e.target.checked;
                            return;
                        }
                        
                        // Toggle control state
                        if (this.activeControls.has(controlId)) {
                            this.activeControls.delete(controlId);
                        } else {
                            this.activeControls.add(controlId);
                        }
                        
                        // Trigger metrics update if needed
                        if (typeof this.recalculateMetrics === 'function') {
                            await this.recalculateMetrics();
                        }
                        
                        // Trigger auto-save if scheduleAutoSave method exists
                        if (typeof this.scheduleAutoSave === 'function') {
                            this.scheduleAutoSave();
                        }
                    });
                }
            });
        }
    }
    
    async toggleCapability(capability) {
        if (!capability || !capability.capability_id) {
            console.error('❌ Invalid capability object:', capability);
            return;
        }
        
        // Ensure activeCapabilities is initialized
        if (!this.activeCapabilities) {
            this.activeCapabilities = new Set();
        }
        
        // Ensure activeControls is initialized
        if (!this.activeControls) {
            this.activeControls = new Set();
        }
        
        const wasActive = this.activeCapabilities.has(capability.capability_id);
        
        if (wasActive) {
            this.activeCapabilities.delete(capability.capability_id);
            // When capability is deactivated, deactivate all its controls
            if (capability.controls) {
                capability.controls.forEach(control => {
                    this.activeControls.delete(control.control_id);
                });
            }
        } else {
            this.activeCapabilities.add(capability.capability_id);
            // When capability is activated, activate all its controls by default
            if (capability.controls) {
                capability.controls.forEach(control => {
                    this.activeControls.add(control.control_id);
                });
            }
        }
        
        // Recreate tree to update visual state
        this.createVerticalTree();
        
        // Recalculate metrics if method exists
        if (typeof this.recalculateMetrics === 'function') {
            await this.recalculateMetrics();
        }
        
        // Update debug info if method exists
        if (typeof this.updateDebugInfo === 'function') {
            this.updateDebugInfo();
        }
        
        // Update save status if method exists
        if (typeof this.updateSaveStatus === 'function') {
            this.updateSaveStatus('unsaved');
        }
        
        // Trigger auto-save if scheduleAutoSave method exists
        if (typeof this.scheduleAutoSave === 'function') {
            this.scheduleAutoSave();
        }
    }
    
    // Serialize control selections for saving scenarios
    serializeControlSelections() {
        // Serialize ALL controls from active capabilities, not just active ones
        // This allows us to track granular enable/disable states per control
        // Use a Map to deduplicate by control_id (a control can appear in multiple capabilities)
        const controlSelectionsMap = new Map();
        
        if (!this.treeData) {
            return [];
        }
        
        // Ensure activeControls is initialized
        if (!this.activeControls) {
            this.activeControls = new Set();
        }
        
        // Iterate through all active capabilities
        if (this.activeCapabilities) {
            this.activeCapabilities.forEach(capabilityId => {
                const capability = this.treeData.find(cap => cap.capability_id === capabilityId);
                if (capability && capability.controls) {
                    capability.controls.forEach(control => {
                        // Validate control has a valid control_id
                        if (control && control.control_id) {
                            // Use control_id as key to deduplicate
                            // If control appears in multiple capabilities, keep the first is_active value
                            // (or we could use OR logic - if active in any capability, mark as active)
                            if (!controlSelectionsMap.has(control.control_id)) {
                                const isActive = this.activeControls.has(control.control_id);
                                controlSelectionsMap.set(control.control_id, {
                                    control_id: control.control_id,
                                    is_active: isActive
                                });
                            } else {
                                // If control already exists, use OR logic for is_active
                                // (if active in any capability, it should be active)
                                const existing = controlSelectionsMap.get(control.control_id);
                                const isActive = this.activeControls.has(control.control_id);
                                if (isActive && !existing.is_active) {
                                    existing.is_active = true;
                                }
                            }
                        } else {
                            console.warn('Invalid control found in capability:', capabilityId, control);
                        }
                    });
                }
            });
        }
        
        // Convert Map to Array
        const controlSelections = Array.from(controlSelectionsMap.values());
        return controlSelections;
    }
    
    // Filter methods for capability search and filtering
    filterBySearch(searchTerm) {
        this.searchTerm = searchTerm.toLowerCase().trim();
        if (this.treeData) {
            this.createVerticalTree();
            if (typeof this.updateDebugInfo === 'function') {
                this.updateDebugInfo();
            }
        }
    }
    
    clearSearch() {
        const searchInput = document.getElementById('search-filter');
        if (searchInput) {
            searchInput.value = '';
        }
        this.searchTerm = '';
        if (this.treeData) {
            this.createVerticalTree();
            if (typeof this.updateDebugInfo === 'function') {
                this.updateDebugInfo();
            }
        }
    }
    
    filterByType(type) {
        this.selectedType = type || '';
        if (this.treeData) {
            this.createVerticalTree();
            if (typeof this.updateDebugInfo === 'function') {
                this.updateDebugInfo();
            }
        }
    }
    
    filterByDomain(domain) {
        this.selectedDomain = domain || '';
        if (this.treeData) {
            this.createVerticalTree();
            if (typeof this.updateDebugInfo === 'function') {
                this.updateDebugInfo();
            }
        }
    }
    
    sortByOption(sortBy) {
        this.sortBy = sortBy || 'type-name';
        if (this.treeData) {
            this.createVerticalTree();
            if (typeof this.updateDebugInfo === 'function') {
                this.updateDebugInfo();
            }
        }
    }
}
