class DashboardGapsView extends DashboardRiskViews {
    renderGaps() {
        if (!this.data || !this.data.gaps) return;
        
        const summary = this.data.gaps.summary;
        if (!summary) return;
        
        // Safely update gap count elements
        const unmappedRisksEl = document.getElementById('unmappedRisksCount');
        const riskCoverageEl = document.getElementById('riskCoveragePct');
        if (unmappedRisksEl) unmappedRisksEl.textContent = summary.unmapped_risks || 0;
        if (riskCoverageEl) riskCoverageEl.textContent = `${summary.risk_coverage_pct || 0}% coverage`;
        
        const unmappedControlsEl = document.getElementById('unmappedControlsCount');
        const controlUtilizationEl = document.getElementById('controlUtilizationPct');
        if (unmappedControlsEl) unmappedControlsEl.textContent = summary.unmapped_controls || 0;
        if (controlUtilizationEl) controlUtilizationEl.textContent = `${summary.control_utilization_pct || 0}% utilized`;
        
        const unmappedQuestionsEl = document.getElementById('unmappedQuestionsCount');
        const questionCoverageEl = document.getElementById('questionCoveragePct');
        if (unmappedQuestionsEl) unmappedQuestionsEl.textContent = summary.unmapped_questions || 0;
        if (questionCoverageEl) questionCoverageEl.textContent = `${summary.question_coverage_pct || 0}% coverage`;
        
        const risksWithoutQuestionsEl = document.getElementById('risksWithoutQuestionsCount');
        const risksWithoutQuestionsPctEl = document.getElementById('risksWithoutQuestionsPct');
        if (risksWithoutQuestionsEl) risksWithoutQuestionsEl.textContent = summary.risks_without_questions || 0;
        if (risksWithoutQuestionsPctEl) risksWithoutQuestionsPctEl.textContent = `${summary.risks_without_questions_pct || 0}% of risks`;
        
        const controlsWithoutQuestionsEl = document.getElementById('controlsWithoutQuestionsCount');
        const controlsWithoutQuestionsPctEl = document.getElementById('controlsWithoutQuestionsPct');
        if (controlsWithoutQuestionsEl) controlsWithoutQuestionsEl.textContent = summary.controls_without_questions || 0;
        if (controlsWithoutQuestionsPctEl) controlsWithoutQuestionsPctEl.textContent = `${summary.controls_without_questions_pct || 0}% of controls`;
        
        const riskCard = document.querySelector('[data-gap-type="risks"]');
        const controlCard = document.querySelector('[data-gap-type="controls"]');
        const questionCard = document.querySelector('[data-gap-type="questions"]');
        const risksWithoutQuestionsCard = document.querySelector('[data-gap-type="risks-without-questions"]');
        const controlsWithoutQuestionsCard = document.querySelector('[data-gap-type="controls-without-questions"]');
        
        [riskCard, controlCard, questionCard, risksWithoutQuestionsCard, controlsWithoutQuestionsCard].forEach(card => {
            if (card) card.classList.remove('success');
        });
        
        if (riskCard && summary.unmapped_risks === 0) riskCard.classList.add('success');
        if (controlCard && summary.unmapped_controls === 0) controlCard.classList.add('success');
        if (questionCard && summary.unmapped_questions === 0) questionCard.classList.add('success');
        if (risksWithoutQuestionsCard && (summary.risks_without_questions || 0) === 0) risksWithoutQuestionsCard.classList.add('success');
        if (controlsWithoutQuestionsCard && (summary.controls_without_questions || 0) === 0) controlsWithoutQuestionsCard.classList.add('success');
        
        // Only render detail tables if data exists
        // Note: The API returns data at top level, not in a "details" object
        if (this.data.gaps) {
            this.renderUnmappedRisks();
            this.renderUnmappedControls();
            this.renderUnmappedQuestions();
            this.renderRisksWithoutQuestions();
            this.renderControlsWithoutQuestions();
        }
    }

    switchGapsTab(tabName) {
        document.querySelectorAll('.clickable-gap-card').forEach(card => card.classList.remove('active'));
        const targetCard = document.querySelector(`[data-gap-type="${tabName}"]`);
        if (!targetCard) return;
        targetCard.classList.add('active');

        document.querySelectorAll('.gaps-tab-content').forEach(content => content.classList.remove('active'));
        
        let targetId;
        if (tabName === 'risks-without-questions') {
            targetId = 'gapsRisksWithoutQuestions';
        } else if (tabName === 'controls-without-questions') {
            targetId = 'gapsControlsWithoutQuestions';
        } else {
            targetId = `gaps${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`;
        }
        
        const targetContent = document.getElementById(targetId);
        if (!targetContent) return;
        targetContent.classList.add('active', 'fade-in');
        
        // Re-render the table when switching tabs
        if (tabName === 'risks') {
            this.renderUnmappedRisks();
        } else if (tabName === 'controls') {
            this.renderUnmappedControls();
        } else if (tabName === 'questions') {
            this.renderUnmappedQuestions();
        } else if (tabName === 'risks-without-questions') {
            this.renderRisksWithoutQuestions();
        } else if (tabName === 'controls-without-questions') {
            this.renderControlsWithoutQuestions();
        }
        
        setTimeout(() => targetContent.classList.remove('fade-in'), 500);
    }
    
    renderUnmappedRisks() {
        if (!this.data?.gaps?.unmapped_risks) return;
        
        const tbody = document.querySelector('#unmappedRisksTable');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        this.data.gaps.unmapped_risks.forEach((item) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.risk_id || ''}</td>
                <td>${item.risk_title || ''}</td>
                <td>${item.risk_description || ''}</td>
            `;
            tbody.appendChild(row);
        });
    }

    renderUnmappedControls() {
        if (!this.data?.gaps?.unmapped_controls) return;
        
        const tbody = document.querySelector('#unmappedControlsTable');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        this.data.gaps.unmapped_controls.forEach((item) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.control_id || ''}</td>
                <td>${item.control_title || ''}</td>
                <td>${item.control_description || ''}</td>
            `;
            tbody.appendChild(row);
        });
    }

    renderUnmappedQuestions() {
        if (!this.data?.gaps?.unmapped_questions) return;
        
        const tbody = document.querySelector('#unmappedQuestionsTable');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        this.data.gaps.unmapped_questions.forEach((item) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.question_id || ''}</td>
                <td>${item.question_text || ''}</td>
                <td>${item.category || ''}</td>
            `;
            tbody.appendChild(row);
        });
    }

    renderRisksWithoutQuestions() {
        if (!this.data?.gaps?.risks_without_questions) return;
        
        const tbody = document.querySelector('#risksWithoutQuestionsTable');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        this.data.gaps.risks_without_questions.forEach((item) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.risk_id || ''}</td>
                <td>${item.risk_title || ''}</td>
                <td>${item.risk_description || ''}</td>
            `;
            tbody.appendChild(row);
        });
    }

    renderControlsWithoutQuestions() {
        if (!this.data?.gaps?.controls_without_questions) return;
        
        const tbody = document.querySelector('#controlsWithoutQuestionsTable');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        this.data.gaps.controls_without_questions.forEach((item) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.control_id || ''}</td>
                <td>${item.control_title || ''}</td>
                <td>${item.control_description || ''}</td>
            `;
            tbody.appendChild(row);
        });
    }
}
