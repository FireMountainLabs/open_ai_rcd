class DashboardRiskViews extends DashboardSearch {
    renderRiskDistribution() {
        const container = document.getElementById('riskDistributionChart');
        container.innerHTML = '';
        
        if (!this.data.risks || !this.data.risks.stats) return;
        
        const data = this.data.risks.stats;
        const totalRisks = data.reduce((sum, item) => sum + item.count, 0);
        
        const svg = d3.select(container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', window.getConfig('ui.chart_height', 200))
            .attr('viewBox', `0 0 ${window.getConfig('ui.chart_width', 600)} ${window.getConfig('ui.chart_height', 200)}`);
        
        const margin = { top: 20, right: 30, bottom: 40, left: 100 };
        const width = window.getConfig('ui.chart_width', 600) - margin.left - margin.right;
        const height = window.getConfig('ui.chart_height', 200) - margin.top - margin.bottom;
        
        const g = svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);
        
        const xScale = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.count)])
            .range([0, width]);
        
        const yScale = d3.scaleBand()
            .domain(data.map(d => d.risk_prefix))
            .range([0, height])
            .padding(0.1);
        
        g.selectAll('.bar')
            .data(data)
            .enter().append('rect')
            .attr('class', 'bar')
            .attr('x', 0)
            .attr('y', d => yScale(d.risk_prefix))
            .attr('width', d => xScale(d.count))
            .attr('height', yScale.bandwidth())
            .attr('fill', window.DashboardConfig?.visualization?.colors?.risk || '#ffbf00')
            .attr('opacity', 0.7);
        
        g.selectAll('.label')
            .data(data)
            .enter().append('text')
            .attr('class', 'label')
            .attr('x', d => xScale(d.count) + 5)
            .attr('y', d => yScale(d.risk_prefix) + yScale.bandwidth() / 2)
            .attr('dy', '0.35em')
            .style('font-size', '12px')
            .style('fill', window.DashboardConfig?.visualization?.colors?.text || '#333')
            .text(d => d.count);
        
        g.append('g')
            .attr('transform', `translate(0,${height})`)
            .call(d3.axisBottom(xScale))
            .style('font-size', '10px');
        
        g.append('g')
            .call(d3.axisLeft(yScale))
            .style('font-size', '10px');
        
        g.append('text')
            .attr('x', width / 2)
            .attr('y', -5)
            .attr('text-anchor', 'middle')
            .style('font-size', '14px')
            .style('font-weight', 'bold')
            .text(`Total: ${totalRisks} risks across ${data.length} categories`);
    }

    renderCoverageAnalysis() {
        this.renderCoverageChart('riskCoverageChart', 'Risk Coverage', this.data.gaps.summary.risk_coverage_pct);
        this.renderCoverageChart('controlUtilizationChart', 'Control Utilization', this.data.gaps.summary.control_utilization_pct);
    }

    renderCoverageChart(containerId, title, percentage) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';
        
        const svg = d3.select(container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', window.getConfig('ui.chart_height', 200) * 0.75)
            .attr('viewBox', `0 0 300 ${window.getConfig('ui.chart_height', 200) * 0.75}`);
        
        const centerX = 150;
        const centerY = 75;
        const radius = 50;
        
        svg.append('circle')
            .attr('cx', centerX)
            .attr('cy', centerY)
            .attr('r', radius)
            .attr('fill', '#e0e0e0');
        
        const arc = d3.arc()
            .innerRadius(0)
            .outerRadius(radius)
            .startAngle(0)
            .endAngle(2 * Math.PI * (percentage / 100));
            
        svg.append('path')
            .attr('d', arc)
            .attr('transform', `translate(${centerX}, ${centerY})`)
            .attr('fill', window.DashboardConfig?.visualization?.colors?.primary || '#3b82f6');

        svg.append('text')
            .attr('x', centerX)
            .attr('y', centerY)
            .attr('text-anchor', 'middle')
            .attr('dy', '0.3em')
            .style('font-size', '20px')
            .style('font-weight', 'bold')
            .text(`${percentage.toFixed(1)}%`);
            
        svg.append('text')
            .attr('x', centerX)
            .attr('y', centerY + radius + 20)
            .attr('text-anchor', 'middle')
            .style('font-size', '14px')
            .text(title);
    }
}
