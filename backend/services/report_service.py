"""
Сервис для генерации отчётов
"""
import logging
from datetime import datetime
from typing import Optional, List
from jinja2 import Template
from backend.config import settings
from backend.models.schemas import CompetitorAnalysis, ImageAnalysis

logger = logging.getLogger("competitor_monitor.report")

# HTML шаблон отчёта
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Отчёт анализа конкурента</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; border-bottom: 2px solid #06b6d4; padding-bottom: 10px; }
        h2 { color: #06b6d4; margin-top: 30px; }
        .section { background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 10px 0; }
        .strengths { border-left: 4px solid #10b981; }
        .weaknesses { border-left: 4px solid #ef4444; }
        .recommendations { border-left: 4px solid #f59e0b; }
        ul { padding-left: 20px; }
        li { margin: 8px 0; }
        .meta { color: #666; font-size: 14px; }
        .score { font-size: 24px; font-weight: bold; color: #06b6d4; }
        .summary { background: linear-gradient(135deg, #06b6d420, #8b5cf620); padding: 20px; border-radius: 8px; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }
    </style>
</head>
<body>
    <h1>📊 Отчёт анализа конкурента</h1>
    <p class="meta">Дата: {{ date }} | Тип анализа: {{ analysis_type }}</p>
    
    {% if summary %}
    <div class="summary">
        <h2>📌 Резюме</h2>
        <p>{{ summary }}</p>
    </div>
    {% endif %}
    
    {% if strengths %}
    <div class="section strengths">
        <h2>✅ Сильные стороны</h2>
        <ul>
        {% for item in strengths %}
            <li>{{ item }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    {% if weaknesses %}
    <div class="section weaknesses">
        <h2>⚠️ Слабые стороны</h2>
        <ul>
        {% for item in weaknesses %}
            <li>{{ item }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    {% if unique_offers %}
    <div class="section">
        <h2>🎯 Уникальные предложения</h2>
        <ul>
        {% for item in unique_offers %}
            <li>{{ item }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    {% if recommendations %}
    <div class="section recommendations">
        <h2>💡 Рекомендации</h2>
        <ul>
        {% for item in recommendations %}
            <li>{{ item }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    {% if marketing_insights %}
    <div class="section">
        <h2>👁️ Маркетинговые инсайты</h2>
        <ul>
        {% for item in marketing_insights %}
            <li>{{ item }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    {% if visual_style_score %}
    <div class="section">
        <h2>🎨 Оценка визуального стиля</h2>
        <p class="score">{{ visual_style_score }}/10</p>
        <p>{{ visual_style_analysis }}</p>
    </div>
    {% endif %}
    
    <div class="footer">
        <p>Сгенерировано CompetitorAI • {{ date }}</p>
    </div>
</body>
</html>
"""

# Markdown шаблон
MARKDOWN_TEMPLATE = """
# 📊 Отчёт анализа конкурента

**Дата:** {{ date }}  
**Тип анализа:** {{ analysis_type }}

---

{% if summary %}
## 📌 Резюме

{{ summary }}

---
{% endif %}

{% if strengths %}
## ✅ Сильные стороны

{% for item in strengths %}
- {{ item }}
{% endfor %}

---
{% endif %}

{% if weaknesses %}
## ⚠️ Слабые стороны

{% for item in weaknesses %}
- {{ item }}
{% endfor %}

---
{% endif %}

{% if unique_offers %}
## 🎯 Уникальные предложения

{% for item in unique_offers %}
- {{ item }}
{% endfor %}

---
{% endif %}

{% if recommendations %}
## 💡 Рекомендации

{% for item in recommendations %}
- {{ item }}
{% endfor %}

---
{% endif %}

{% if marketing_insights %}
## 👁️ Маркетинговые инсайты

{% for item in marketing_insights %}
- {{ item }}
{% endfor %}

---
{% endif %}

{% if visual_style_score %}
## 🎨 Оценка визуального стиля

**Оценка:** {{ visual_style_score }}/10

{{ visual_style_analysis }}

---
{% endif %}

---

*Сгенерировано CompetitorAI • {{ date }}*
"""


class ReportService:
    """Генерация отчётов в различных форматах"""
    
    def __init__(self):
        logger.info("=" * 50)
        logger.info("Инициализация Report сервиса")
        logger.info("Report сервис инициализирован ✓")
        logger.info("=" * 50)
    
    def _prepare_data(self, analysis) -> dict:
        """Подготовить данные из анализа"""
        data = {
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "analysis_type": type(analysis).__name__.replace("Analysis", ""),
            "summary": getattr(analysis, 'summary', '') or '',
            "strengths": getattr(analysis, 'strengths', []) or [],
            "weaknesses": getattr(analysis, 'weaknesses', []) or [],
            "unique_offers": getattr(analysis, 'unique_offers', []) or [],
            "recommendations": getattr(analysis, 'recommendations', []) or [],
            "marketing_insights": getattr(analysis, 'marketing_insights', []) or [],
            "visual_style_score": getattr(analysis, 'visual_style_score', 0) or 0,
            "visual_style_analysis": getattr(analysis, 'visual_style_analysis', '') or '',
        }
        return data
    
    def generate_html(self, analysis) -> str:
        """
        Генерировать HTML отчёт
        
        Args:
            analysis: Объект анализа (CompetitorAnalysis или ImageAnalysis)
            
        Returns:
            HTML код отчёта
        """
        logger.info("📄 Генерация HTML отчёта")
        
        data = self._prepare_data(analysis)
        template = Template(HTML_TEMPLATE)
        html = template.render(**data)
        
        logger.info(f"  ✓ HTML сгенерирован: {len(html)} символов")
        return html
    
    def generate_markdown(self, analysis) -> str:
        """
        Генерировать Markdown отчёт
        
        Args:
            analysis: Объект анализа
            
        Returns:
            Markdown текст отчёта
        """
        logger.info("📝 Генерация Markdown отчёта")
        
        data = self._prepare_data(analysis)
        template = Template(MARKDOWN_TEMPLATE)
        md = template.render(**data)
        
        logger.info(f"  ✓ Markdown сгенерирован: {len(md)} символов")
        return md
    
    def generate_pdf(self, analysis) -> bytes:
        """
        Генерировать PDF отчёт
        
        Args:
            analysis: Объект анализа
            
        Returns:
            PDF файл в байтах
        """
        logger.info("📑 Генерация PDF отчёта")
        
        try:
            from weasyprint import HTML
            
            html = self.generate_html(analysis)
            
            # Конвертируем HTML в PDF
            pdf_bytes = HTML(string=html).write_pdf()
            
            logger.info(f"  ✓ PDF сгенерирован: {len(pdf_bytes)} байт")
            return pdf_bytes
            
        except ImportError:
            logger.error("  ✗ WeasyPrint не установлен")
            raise Exception("Для генерации PDF установите weasyprint: pip install weasyprint")
        except Exception as e:
            logger.error(f"  ✗ Ошибка генерации PDF: {e}")
            raise

# Глобальный экземпляр
report_service = ReportService()