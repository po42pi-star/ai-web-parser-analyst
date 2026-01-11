"""
Сервис для генерации визуализаций (графиков)
"""
import base64
import logging
import io
from typing import Optional, List
import matplotlib
matplotlib.use('Agg')  # Без GUI
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon
import numpy as np
from backend.models.schemas import CompetitorAnalysis, ImageAnalysis

logger = logging.getLogger("competitor_monitor.visualization")

# Цветовая схема
COLORS = {
    'strengths': '#10b981',      # Зелёный
    'weaknesses': '#ef4444',     # Красный
    'recommendations': '#f59e0b', # Оранжевый
    'unique': '#8b5cf6',         # Фиолетовый
    'insights': '#06b6d4',       # Голубой
}


class VisualizationService:
    """Генерация графиков и визуализаций"""
    
    def __init__(self):
        logger.info("=" * 50)
        logger.info("Инициализация Visualization сервиса")
        
        # Настройка matplotlib для красивых графиков
        plt.style.use('dark_background')
        plt.rcParams.update({
            'font.size': 10,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'figure.facecolor': '#1a2234',
            'axes.facecolor': '#1a2234',
            'text.color': '#f1f5f9',
            'axes.labelcolor': '#f1f5f9',
            'xtick.color': '#94a3b8',
            'ytick.color': '#94a3b8',
            'axes.edgecolor': '#334155',
            'axes.titlecolor': '#f1f5f9',
        })
        
        logger.info("Visualization сервис инициализирован ✓")
        logger.info("=" * 50)
    
    def _list_to_scores(self, items: List[str]) -> List[float]:
        """Конвертировать список в оценки (1-10)"""
        if not items:
            return []
        # Каждый элемент = 1 балл, максимум 10
        return [min(i + 1, 10) for i in range(len(items))]
    
    def generate_radar_chart(
        self,
        strengths: List[str],
        weaknesses: List[str],
        unique_offers: List[str],
        recommendations: List[str],
        title: str = "Анализ конкурента"
    ) -> str:
        """
        Генерировать Radar Chart (паутина)
        
        Args:
            strengths: Сильные стороны
            weaknesses: Слабые стороны
            unique_offers: Уникальные предложения
            recommendations: Рекомендации
            title: Заголовок графика
            
        Returns:
            Base64 изображение графика
        """
        logger.info("📊 Генерация Radar Chart")
        
        # Подготавливаем данные
        categories = []
        values = []
        
        if strengths:
            categories.append('Сильные стороны')
            values.append(min(len(strengths) * 2, 10))
        if weaknesses:
            categories.append('Слабые стороны')
            values.append(10 - min(len(weaknesses) * 2, 9))
        if unique_offers:
            categories.append('Уникальные предложения')
            values.append(min(len(unique_offers) * 2, 10))
        if recommendations:
            categories.append('Рекомендации')
            values.append(min(len(recommendations) * 2, 10))
        
        if len(categories) < 3:
            logger.warning("  ⚠️ Недостаточно данных для Radar Chart")
            return None
        
        # Закрываем полигон
        categories.append(categories[0])
        values.append(values[0])
        
        # Создаём график
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        
        # Углы для категорий
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]
        values += values[:1]
        
        # Рисуем полигон
        ax.fill(angles, values, color='#06b6d4', alpha=0.25)
        ax.plot(angles, values, color='#06b6d4', linewidth=2)
        
        # Добавляем сетку
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories[:-1], size=10)
        ax.set_ylim(0, 10)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(['2', '4', '6', '8', '10'], color='#64748b', size=8)
        
        # Заголовок
        ax.set_title(title, size=16, color='#f1f5f9', pad=20)
        
        # Сохраняем в base64
        buffer = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buffer, format='png', dpi=150, facecolor='#1a2234', edgecolor='none')
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)
        
        logger.info(f"  ✓ Radar Chart сгенерирован: {len(img_base64)} символов base64")
        return img_base64
    
    def generate_comparison_bar_chart(
        self,
        analysis: CompetitorAnalysis,
        title: str = "Сравнение характеристик"
    ) -> str:
        """
        Генерировать Bar Chart сравнения
        
        Args:
            analysis: Объект анализа
            title: Заголовок
            
        Returns:
            Base64 изображение графика
        """
        logger.info("📊 Генерация Bar Chart")
        
        # Данные для сравнения
        categories = ['Сильные стороны', 'Слабые стороны', 'УТП', 'Рекомендации']
        values = [
            len(analysis.strengths),
            len(analysis.weaknesses),
            len(analysis.unique_offers),
            len(analysis.recommendations)
        ]
        
        # Создаём график
        fig, ax = plt.subplots(figsize=(10, 6))
        
        colors = ['#10b981', '#ef4444', '#8b5cf6', '#f59e0b']
        bars = ax.bar(categories, values, color=colors, edgecolor='#334155', linewidth=1.5)
        
        # Добавляем значения на столбцы
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.annotate(
                f'{val}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 5),
                textcoords="offset points",
                ha='center', va='bottom',
                fontsize=14, fontweight='bold', color='#f1f5f9'
            )
        
        ax.set_ylabel('Количество', color='#94a3b8')
        ax.set_title(title, size=16, color='#f1f5f9', pad=15)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#334155')
        ax.spines['bottom'].set_color('#334155')
        ax.tick_params(colors='#94a3b8')
        
        # Сохраняем
        buffer = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buffer, format='png', dpi=150, facecolor='#1a2234', edgecolor='none')
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)
        
        logger.info(f"  ✓ Bar Chart сгенерирован: {len(img_base64)} символов base64")
        return img_base64
    
    def generate_visual_score_chart(self, score: int) -> str:
        """
        Генерировать круговую диаграмму оценки
        
        Args:
            score: Оценка от 0 до 10
            
        Returns:
            Base64 изображение
        """
        logger.info(f"📊 Генерация Score Chart: {score}/10")
        
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        
        # Данные
        angles = np.linspace(0, 2 * np.pi, 100)
        score_angle = (score / 10) * 2 * np.pi
        
        # Фон
        ax.fill(angles, [1] * len(angles), color='#1e293b', alpha=0.5)
        
        # Заполненная часть
        filled_angles = np.linspace(0, score_angle, 50)
        ax.fill(filled_angles, [1] * len(filled_angles), color='#06b6d4', alpha=0.8)
        
        # Центральный текст
        ax.text(0, 0, f'{score}/10', ha='center', va='center', 
                fontsize=36, fontweight='bold', color='#06b6d4')
        ax.text(0, -0.15, 'Оценка', ha='center', va='center', 
                fontsize=14, color='#94a3b8')
        
        ax.set_ylim(0, 1.2)
        ax.axis('off')
        
        buffer = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buffer, format='png', dpi=150, facecolor='#1a2234', edgecolor='none')
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)
        
        logger.info(f"  ✓ Score Chart сгенерирован")
        return img_base64

# Глобальный экземпляр
viz_service = VisualizationService()