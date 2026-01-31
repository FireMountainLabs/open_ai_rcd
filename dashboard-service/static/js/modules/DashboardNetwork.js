class DashboardNetwork extends DashboardGapsView {
    renderNetwork(layout = 'force') {
        const container = document.getElementById('networkContainer');
        container.innerHTML = '';

        const width = container.clientWidth;
        const height = container.clientHeight;

        const svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        this.zoomBehavior = d3.zoom()
            .scaleExtent([0.1, 10])
            .on('zoom', (event) => {
                this.currentZoom = event.transform;
                this.updateZoomTransform(event.transform);
                this.updateZoomLevel(event.transform.k);
            });

        svg.call(this.zoomBehavior);

        this.addZoomLevelIndicator(container);

        document.querySelectorAll('.layout-controls .btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`#layout${layout.charAt(0).toUpperCase() + layout.slice(1)}`).classList.add('active');

        switch (layout) {
            case 'force':
                this.renderForceLayout(svg, width, height);
                break;
            case 'hierarchical':
                this.renderHierarchicalLayout(svg, width, height);
                break;
            case 'sankey':
                this.renderSankeyLayout(svg, width, height);
                break;
        }
    }

    renderForceLayout(svg, width, height) {
        document.getElementById('sankeyControls').style.display = 'none';
        
        const nodes = [];
        const links = [];

        this.data.risks.details.forEach(risk => {
            nodes.push({ id: risk.risk_id, title: risk.risk_title, type: 'risk', group: 'Risk' });
        });

        this.data.controls.details.forEach(control => {
            nodes.push({ id: control.control_id, title: control.control_title, type: 'control', group: control.control_type });
        });

        this.data.questions.details.forEach(question => {
            nodes.push({ id: question.question_id, title: question.question_text.substring(0, 50) + '...', type: 'question', group: question.category });
        });

        this.data.network.risk_control_links.forEach(link => {
            links.push({ source: link.risk_id, target: link.control_id, type: 'risk-control' });
        });

        this.data.network.question_risk_links.forEach(link => {
            links.push({ source: link.question_id, target: link.risk_id, type: 'question-risk' });
        });
    }
}
