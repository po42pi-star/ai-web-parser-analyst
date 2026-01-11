"""
Pydantic схемы для API
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# === Запросы ===

class TextAnalysisRequest(BaseModel):
    """Запрос на анализ текста"""
    text: str = Field(..., min_length=10, description="Текст для анализа")


class ParseDemoRequest(BaseModel):
    """Запрос на парсинг URL"""
    url: str = Field(..., description="URL для парсинга")


# === Ответы ===

class CompetitorAnalysis(BaseModel):
    """Структурированный анализ конкурента"""
    strengths: List[str] = Field(default_factory=list, description="Сильные стороны")
    weaknesses: List[str] = Field(default_factory=list, description="Слабые стороны")
    unique_offers: List[str] = Field(default_factory=list, description="Уникальные предложения")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации")
    summary: str = Field("", description="Общее резюме")
    design_score: int = Field(0, ge=0, le=10, description="Оценка дизайна (0-10)")
    technology_potential: int = Field(0, ge=0, le=10, description="Технологический потенциал (0-10)")


class ImageAnalysis(BaseModel):
    """Анализ изображения"""
    description: str = Field("", description="Описание изображения")
    marketing_insights: List[str] = Field(default_factory=list, description="Маркетинговые инсайты")
    visual_style_score: int = Field(0, ge=0, le=10, description="Оценка визуального стиля (0-10)")
    visual_style_analysis: str = Field("", description="Анализ визуального стиля")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации")
    design_score: int = Field(0, ge=0, le=10, description="Оценка дизайна (0-10)")
    technology_potential: int = Field(0, ge=0, le=10, description="Технологический потенциал (0-10)")

class ParsedContent(BaseModel):
    """Результат парсинга страницы"""
    url: str
    title: Optional[str] = None
    h1: Optional[str] = None
    first_paragraph: Optional[str] = None
    analysis: Optional[CompetitorAnalysis] = None
    error: Optional[str] = None


class TextAnalysisResponse(BaseModel):
    """Ответ на анализ текста"""
    success: bool
    analysis: Optional[CompetitorAnalysis] = None
    error: Optional[str] = None


class ImageAnalysisResponse(BaseModel):
    """Ответ на анализ изображения"""
    success: bool
    analysis: Optional[ImageAnalysis] = None
    error: Optional[str] = None


class ParseDemoResponse(BaseModel):
    """Ответ на парсинг"""
    success: bool
    data: Optional[ParsedContent] = None
    error: Optional[str] = None


# === История ===

class HistoryItem(BaseModel):
    """Элемент истории"""
    id: str
    timestamp: datetime
    request_type: str  # "text", "image", "parse"
    request_summary: str
    response_summary: str


class HistoryResponse(BaseModel):
    """Ответ со списком истории"""
    items: List[HistoryItem]
    total: int

# === PDF ===
class PDFAnalysisRequest(BaseModel):
    """Запрос на анализ PDF файла"""
    pass  # Файл передаётся как UploadFile

class PDFAnalysisResponse(BaseModel):
    """Ответ на анализ PDF"""
    success: bool
    extracted_text: Optional[str] = None
    analysis: Optional[CompetitorAnalysis] = None
    error: Optional[str] = None

# === Report ===
class ReportRequest(BaseModel):
    """Запрос на генерацию отчёта"""
    analysis_data: dict  # Данные анализа для отчёта
    format: str = "html"  # html, markdown, pdf

class ReportResponse(BaseModel):
    """Ответ сгенерированным отчётом"""
    success: bool
    format: str
    content: Optional[str] = None  # Для HTML/Markdown (base64 для PDF)
    filename: Optional[str] = None
    error: Optional[str] = None

# === Visualization ===
class VisualizationRequest(BaseModel):
    """Запрос на генерацию визуализации"""
    analysis_data: dict
    chart_type: str = "radar"  # radar, bar, score

class VisualizationResponse(BaseModel):
    """Ответ с изображением визуализации"""
    success: bool
    chart_type: str
    image_base64: Optional[str] = None
    error: Optional[str] = None