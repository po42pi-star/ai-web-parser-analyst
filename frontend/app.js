/**
* Competitor Monitor - Frontend Application
* Мониторинг конкурентов - MVP ассистент
*/
// === State ===
const state = {
    currentTab: 'text',
    selectedImage: null,
    isLoading: false,
    currentAnalysis: null
};
// === DOM Elements ===
const elements = {
    // Navigation
    navButtons: document.querySelectorAll('.nav-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    // Text analysis
    competitorText: document.getElementById('competitor-text'),
    analyzeTextBtn: document.getElementById('analyze-text-btn'),
    // Image analysis
    uploadZone: document.getElementById('upload-zone'),
    imageInput: document.getElementById('image-input'),
    previewContainer: document.getElementById('preview-container'),
    imagePreview: document.getElementById('image-preview'),
    removeImageBtn: document.getElementById('remove-image'),
    analyzeImageBtn: document.getElementById('analyze-image-btn'),
    // Parse demo
    urlInput: document.getElementById('url-input'),
    parseBtn: document.getElementById('parse-btn'),
    // History
    historyList: document.getElementById('history-list'),
    clearHistoryBtn: document.getElementById('clear-history-btn'),
    // Results
    resultsSection: document.getElementById('results-section'),
    resultsContent: document.getElementById('results-content'),
    closeResultsBtn: document.getElementById('close-results'),
    reportFormat: document.getElementById('report-format'),
    downloadReportBtn: document.getElementById('download-report-btn'),
    // Loading
    loadingOverlay: document.getElementById('loading-overlay')
};
// === API Functions ===
const api = {
    baseUrl: '',
    async analyzeText(text) {
        const response = await fetch(`${this.baseUrl}/analyze_text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        return response.json();
    },
    async analyzeImage(file) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${this.baseUrl}/analyze_image`, {
            method: 'POST',
            body: formData
        });
        return response.json();
    },
    async parseDemo(url) {
        const response = await fetch(`${this.baseUrl}/parse_demo`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        return response.json();
    },
    async getHistory() {
        const response = await fetch(`${this.baseUrl}/history`);
        return response.json();
    },
    async clearHistory() {
        const response = await fetch(`${this.baseUrl}/history`, {
            method: 'DELETE'
        });
        return response.json();
    },
    async generateReport(analysisData, format) {
        const response = await fetch(`${this.baseUrl}/generate_report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ analysis_data: analysisData, format: format })
        });
        return response.json();
    }
};
// === UI Functions ===
const ui = {
    showLoading() {
        state.isLoading = true;
        elements.loadingOverlay.style.display = 'flex';
    },
    hideLoading() {
        state.isLoading = false;
        elements.loadingOverlay.style.display = 'none';
    },
    showTab(tabId) {
        state.currentTab = tabId;
        elements.navButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });
        elements.tabContents.forEach(content => {
            content.classList.toggle('active', content.id === `${tabId}-tab`);
        });
        if (tabId === 'history') {
            this.loadHistory();
        }
    },
    showResults(html) {
        elements.resultsContent.innerHTML = html;
        elements.resultsSection.hidden = false;
        elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
    },
    hideResults() {
        elements.resultsSection.hidden = true;
        state.currentAnalysis = null;
    },
    showError(message) {
        const html = `
<div class="error-message">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
<circle cx="12" cy="12" r="10"/>
<line x1="12" y1="8" x2="12" y2="12"/>
<line x1="12" y1="16" x2="12.01" y2="16"/>
</svg>
<span>${message}</span>
</div>
`;
        this.showResults(html);
    },
    renderTextAnalysis(analysis) {
        return `
${this.renderResultBlock('Сильные стороны', analysis.strengths, 'strengths')}
${this.renderResultBlock('Слабые стороны', analysis.weaknesses, 'weaknesses')}
${this.renderResultBlock('Уникальные предложения', analysis.unique_offers, 'unique')}
${this.renderResultBlock('Рекомендации', analysis.recommendations, 'recommendations')}
${analysis.summary ? `
<div class="result-block result-summary">
<h3>Резюме</h3>
<p>${analysis.summary}</p>
</div>
` : ''}
${this.renderScoreBlock('🎨 Оценка дизайна', analysis.design_score, 'design')}
${this.renderScoreBlock('⚡ Технологический потенциал', analysis.technology_potential, 'tech')}
`;
    },
    renderImageAnalysis(analysis) {
        const scorePercent = (analysis.visual_style_score / 10) * 100;
        return `
<div class="result-block">
<h3>Описание изображения</h3>
<p>${analysis.description}</p>
</div>
<div class="result-block">
<h3>Оценка визуального стиля</h3>
<div class="score-display">
<span class="score-value">${analysis.visual_style_score}/10</span>
<div class="score-bar">
<div class="score-fill" style="width: ${scorePercent}%"></div>
</div>
</div>
<p>${analysis.visual_style_analysis}</p>
</div>
${this.renderResultBlock('Маркетинговые инсайты', analysis.marketing_insights, 'insights')}
${this.renderResultBlock('Рекомендации', analysis.recommendations, 'recommendations')}
${this.renderScoreBlock('🎨 Оценка дизайна', analysis.design_score, 'design')}
${this.renderScoreBlock('⚡ Технологический потенциал', analysis.technology_potential, 'tech')}
`;
    },
    renderParsedContent(data) {
        const parsed = data;
        return `
<div class="parsed-content">
<div class="label">URL:</div>
<div class="value">${parsed.url}</div>
<div class="label">Title:</div>
<div class="value">${parsed.title || 'Не найден'}</div>
<div class="label">H1:</div>
<div class="value">${parsed.h1 || 'Не найден'}</div>
<div class="label">Первый абзац:</div>
<div class="value">${parsed.first_paragraph || 'Не найден'}</div>
</div>
${parsed.analysis ? this.renderTextAnalysis(parsed.analysis) : ''}
`;
    },
    renderResultBlock(title, items, type) {
        if (!items || items.length === 0) return '';
        return `
<div class="result-block">
<h3>${title}</h3>
<ul>
${items.map(item => `<li>${item}</li>`).join('')}
</ul>
</div>
`;
    },
    renderScoreBlock(title, score, type) {
        if (score === undefined || score === null) return '';
        const percent = (score / 10) * 100;
        const color = percent >= 70 ? '#10b981' : percent >= 40 ? '#f59e0b' : '#ef4444';
        return `
<div class="result-block">
<h3>${title}</h3>
<div class="score-display">
<span class="score-value" style="color: ${color}">${score}/10</span>
<div class="score-bar">
<div class="score-fill" style="width: ${percent}%; background: ${color}"></div>
</div>
</div>
</div>
`;
    },
    async loadHistory() {
        try {
            const data = await api.getHistory();
            this.renderHistory(data.items);
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    },
    renderHistory(items) {
        if (!items || items.length === 0) {
            elements.historyList.innerHTML = '<p class="empty-msg">История пуста</p>';
            return;
        }
        const typeLabels = {
            text: 'Анализ текста',
            image: 'Анализ изображения',
            parse: 'Парсинг сайта',
            pdf: 'Анализ PDF'
        };
        elements.historyList.innerHTML = items.map(item => {
            const date = new Date(item.timestamp);
            const timeStr = date.toLocaleString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
            return `
<div class="history-item">
<div class="history-content">
<div class="history-type">${typeLabels[item.request_type] || item.request_type}</div>
<div class="history-summary">${item.request_summary}</div>
</div>
<div class="history-time">${timeStr}</div>
</div>
`;
        }).join('');
    }
};
// === Event Handlers ===
const handlers = {
    handleNavClick(e) {
        const btn = e.target.closest('.nav-btn');
        if (btn) {
            ui.showTab(btn.dataset.tab);
        }
    },
    async handleAnalyzeText() {
        let text = elements.competitorText.value.trim();
        if (!text) {
            ui.showError('Введите текст для анализа');
            return;
        }
        if (text.length < 10) {
            ui.showError('Введите минимум 10 символов');
            return;
        }
        ui.showLoading();
        try {
            const result = await api.analyzeText(text);
            if (result.success && result.analysis) {
                state.currentAnalysis = result.analysis;
                ui.showResults(ui.renderTextAnalysis(result.analysis));
            } else {
                ui.showError(result.error || 'Ошибка анализа');
            }
        } catch (error) {
            ui.showError('Ошибка соединения');
        }
        ui.hideLoading();
    },
    handleUploadClick() {
        elements.imageInput.click();
    },
    handleImageSelect(e) {
        const file = e.target.files[0];
        if (!file) return;
        state.selectedImage = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            elements.imagePreview.src = e.target.result;
            elements.previewContainer.hidden = false;
            elements.uploadZone.querySelector('.upload-content').hidden = true;
            elements.analyzeImageBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    },
    handleDragOver(e) {
        e.preventDefault();
        elements.uploadZone.classList.add('dragover');
    },
    handleDragLeave(e) {
        e.preventDefault();
        elements.uploadZone.classList.remove('dragover');
    },
    handleDrop(e) {
        e.preventDefault();
        elements.uploadZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            state.selectedImage = file;
            const reader = new FileReader();
            reader.onload = (ev) => {
                elements.imagePreview.src = ev.target.result;
                elements.previewContainer.hidden = false;
                elements.uploadZone.querySelector('.upload-content').hidden = true;
                elements.analyzeImageBtn.disabled = false;
            };
            reader.readAsDataURL(file);
        }
    },
    handleRemoveImage() {
        state.selectedImage = null;
        elements.imageInput.value = '';
        elements.imagePreview.src = '';
        elements.previewContainer.hidden = true;
        elements.uploadZone.querySelector('.upload-content').hidden = false;
        elements.analyzeImageBtn.disabled = true;
    },
    async handleAnalyzeImage() {
        if (!state.selectedImage) {
            ui.showError('Выберите изображение');
            return;
        }
        ui.showLoading();
        try {
            const result = await api.analyzeImage(state.selectedImage);
            if (result.success && result.analysis) {
                state.currentAnalysis = result.analysis;
                ui.showResults(ui.renderImageAnalysis(result.analysis));
            } else {
                ui.showError(result.error || 'Ошибка анализа');
            }
        } catch (error) {
            ui.showError('Ошибка соединения');
        }
        ui.hideLoading();
    },
    async handleParse() {
        let url = elements.urlInput.value.trim();
        if (!url) {
            ui.showError('Введите URL');
            return;
        }
        if (!url.startsWith('http')) url = 'https://' + url;
        ui.showLoading();
        try {
            const result = await api.parseDemo(url);
            if (result.success && result.data) {
                state.currentAnalysis = result.data.analysis;
                ui.showResults(ui.renderParsedContent(result.data));
            } else {
                ui.showError(result.error || 'Ошибка парсинга');
            }
        } catch (error) {
            ui.showError('Ошибка соединения');
        }
        ui.hideLoading();
    },
    async handleClearHistory() {
        if (!confirm('Очистить историю?')) return;
        await api.clearHistory();
        ui.renderHistory([]);
    },
    handleCloseResults() {
        ui.hideResults();
    },
    async handleDownloadReport() {
        if (!state.currentAnalysis) {
            ui.showError('Нет данных для отчёта');
            return;
        }
        const format = elements.reportFormat ? elements.reportFormat.value : 'html';
        ui.showLoading();
        try {
            const result = await api.generateReport(state.currentAnalysis, format);
            if (result.success) {
                if (format === 'pdf') {
                    const link = document.createElement('a');
                    link.href = `data:application/pdf;base64,${result.content}`;
                    link.download = result.filename;
                    link.click();
                } else {
                    const blob = new Blob([result.content], {
                        type: format === 'html' ? 'text/html' : 'text/markdown'
                    });
                    const link = document.createElement('a');
                    link.href = URL.createObjectURL(blob);
                    link.download = result.filename;
                    link.click();
                }
            } else {
                ui.showError(result.error || 'Ошибка генерации отчёта');
            }
        } catch (error) {
            ui.showError('Ошибка соединения');
        }
        ui.hideLoading();
    }
};
// === Initialize ===
function init() {
    elements.navButtons.forEach(btn => {
        btn.addEventListener('click', handlers.handleNavClick.bind(handlers));
    });
    elements.analyzeTextBtn.addEventListener('click', handlers.handleAnalyzeText.bind(handlers));
    elements.uploadZone.addEventListener('click', handlers.handleUploadClick.bind(handlers));
    elements.imageInput.addEventListener('change', handlers.handleImageSelect.bind(handlers));
    elements.uploadZone.addEventListener('dragover', handlers.handleDragOver.bind(handlers));
    elements.uploadZone.addEventListener('dragleave', handlers.handleDragLeave.bind(handlers));
    elements.uploadZone.addEventListener('drop', handlers.handleDrop.bind(handlers));
    elements.removeImageBtn.addEventListener('click', handlers.handleRemoveImage.bind(handlers));
    elements.analyzeImageBtn.addEventListener('click', handlers.handleAnalyzeImage.bind(handlers));
    elements.parseBtn.addEventListener('click', handlers.handleParse.bind(handlers));
    elements.urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handlers.handleParse();
    });
    elements.clearHistoryBtn.addEventListener('click', handlers.handleClearHistory.bind(handlers));
    elements.closeResultsBtn.addEventListener('click', handlers.handleCloseResults.bind(handlers));
    if (elements.downloadReportBtn) {
        elements.downloadReportBtn.addEventListener('click', handlers.handleDownloadReport.bind(handlers));
    }
    ui.showTab('text');
}
document.addEventListener('DOMContentLoaded', init);