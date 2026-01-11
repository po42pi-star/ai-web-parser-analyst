"""
Главный модуль FastAPI приложения
Мониторинг конкурентов - MVP ассистент
"""
import base64
import time
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from backend.services.pdf_service import pdf_service
from backend.services.report_service import report_service
from backend.services.visualization_service import viz_service

from backend.config import settings
from backend.models.schemas import (
    TextAnalysisRequest,
    TextAnalysisResponse,
    ImageAnalysisResponse,
    ParseDemoRequest,
    ParseDemoResponse,
    ParsedContent,
    HistoryResponse,
    PDFAnalysisRequest, PDFAnalysisResponse,
    ReportRequest, ReportResponse,
    VisualizationRequest, VisualizationResponse
)
from backend.services.openai_service import openai_service
from backend.services.parser_service import parser_service
from backend.services.history_service import history_service

from backend.services.http_parser_service import http_parser_service

# Логгер для API
logger = logging.getLogger("competitor_monitor.api")

# Инициализация приложения
logger.info("=" * 60)
logger.info("🚀 ЗАПУСК ПРИЛОЖЕНИЯ: Мониторинг конкурентов")
logger.info("=" * 60)

app = FastAPI(
    title="Мониторинг конкурентов",
    description="MVP ассистент для анализа конкурентов с поддержкой текста и изображений",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS для работы с фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("CORS middleware добавлен ✓")


# === Middleware для логирования запросов ===

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирование всех HTTP запросов"""
    start_time = time.time()
    
    # Логируем входящий запрос
    logger.info(f"➡️  {request.method} {request.url.path}")
    if request.query_params:
        logger.debug(f"    Query params: {dict(request.query_params)}")
    
    # Выполняем запрос
    response = await call_next(request)
    
    # Логируем ответ
    elapsed = time.time() - start_time
    status_emoji = "✅" if response.status_code < 400 else "❌"
    logger.info(f"{status_emoji} {request.method} {request.url.path} -> {response.status_code} ({elapsed:.3f}s)")
    
    return response


# === События жизненного цикла ===

@app.on_event("startup")
async def startup_event():
    """Событие при запуске сервера"""
    logger.info("=" * 60)
    logger.info("🟢 СЕРВЕР ЗАПУЩЕН")
    logger.info(f"  Адрес: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"  Документация: http://localhost:{settings.api_port}/docs")
    logger.info(f"  Модель текста: {settings.openai_model}")
    logger.info(f"  Модель vision: {settings.openai_vision_model}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Закрытие ресурсов при остановке сервера"""
    logger.info("=" * 60)
    logger.info("🔴 ОСТАНОВКА СЕРВЕРА")
    logger.info("  Закрытие Parser сервиса...")
    await parser_service.close()
    logger.info("  ✓ Все ресурсы освобождены")
    logger.info("=" * 60)


# === Эндпоинты ===

@app.get("/")
async def root():
    """Главная страница - отдаём фронтенд"""
    logger.debug("Запрос главной страницы")
    return FileResponse("frontend/index.html")


@app.post("/analyze_text", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    Анализ текста конкурента
    """
    logger.info("=" * 50)
    logger.info("📝 API: АНАЛИЗ ТЕКСТА")
    logger.info(f"  Длина текста: {len(request.text)} символов")
    logger.info(f"  Превью: {request.text[:80]}...")
    
    try:
        start_time = time.time()
        
        analysis = await openai_service.analyze_text(request.text)
        
        elapsed = time.time() - start_time
        logger.info(f"  ✓ Анализ завершён за {elapsed:.2f} сек")
        
        # Сохраняем в историю
        logger.info("  💾 Сохранение в историю...")
        history_service.add_entry(
            request_type="text",
            request_summary=request.text[:100] + "..." if len(request.text) > 100 else request.text,
            response_summary=analysis.summary
        )
        
        logger.info("  ✅ УСПЕХ: Анализ текста завершён")
        logger.info("=" * 50)
        
        return TextAnalysisResponse(
            success=True,
            analysis=analysis
        )
    except Exception as e:
        logger.error(f"  ❌ ОШИБКА: {e}")
        logger.error("=" * 50)
        return TextAnalysisResponse(
            success=False,
            error=str(e)
        )


@app.post("/analyze_image", response_model=ImageAnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    """
    Анализ изображения конкурента
    """
    logger.info("=" * 50)
    logger.info("🖼️ API: АНАЛИЗ ИЗОБРАЖЕНИЯ")
    logger.info(f"  Имя файла: {file.filename}")
    logger.info(f"  Тип: {file.content_type}")
    
    # Проверяем тип файла
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        logger.warning(f"  ⚠ Неподдерживаемый тип файла: {file.content_type}")
        logger.info("=" * 50)
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип файла. Разрешены: {', '.join(allowed_types)}"
        )
    
    try:
        start_time = time.time()
        
        # Читаем и кодируем изображение
        logger.info("  📥 Чтение файла...")
        content = await file.read()
        file_size_kb = len(content) / 1024
        logger.info(f"  Размер файла: {file_size_kb:.1f} KB")
        
        image_base64 = base64.b64encode(content).decode('utf-8')
        logger.info(f"  Base64 размер: {len(image_base64)} символов")
        
        # Анализируем
        logger.info("  🔍 Отправка на анализ...")
        analysis = await openai_service.analyze_image(
            image_base64=image_base64,
            mime_type=file.content_type
        )
        
        elapsed = time.time() - start_time
        logger.info(f"  ✓ Анализ завершён за {elapsed:.2f} сек")
        
        # Сохраняем в историю
        logger.info("  💾 Сохранение в историю...")
        history_service.add_entry(
            request_type="image",
            request_summary=f"Изображение: {file.filename}",
            response_summary=analysis.description[:200] if analysis.description else "Анализ изображения"
        )
        
        logger.info("  ✅ УСПЕХ: Анализ изображения завершён")
        logger.info("=" * 50)
        
        return ImageAnalysisResponse(
            success=True,
            analysis=analysis
        )
    except Exception as e:
        logger.error(f"  ❌ ОШИБКА: {e}")
        logger.error("=" * 50)
        return ImageAnalysisResponse(
            success=False,
            error=str(e)
        )


@app.post("/parse_demo", response_model=ParseDemoResponse)
async def parse_demo(request: ParseDemoRequest):
    """
    Парсинг и анализ сайта конкурента через Chrome
    """
    logger.info("=" * 50)
    logger.info("🌐 API: ПАРСИНГ САЙТА")
    logger.info(f"  URL: {request.url}")
    
    try:
        total_start = time.time()
        
        # Открываем страницу в Chrome и делаем скриншот
        logger.info("  🔍 Запуск парсинга...")
        parse_start = time.time()
        title, h1, first_paragraph, screenshot_bytes, error = await parser_service.parse_url(request.url)
        parse_elapsed = time.time() - parse_start
        logger.info(f"  ✓ Парсинг завершён за {parse_elapsed:.2f} сек")
        
        if error:
            logger.error(f"  ❌ Ошибка парсинга: {error}")
            logger.info("=" * 50)
            return ParseDemoResponse(
                success=False,
                error=error
            )
        
        logger.info(f"  📌 Title: {title[:50] if title else 'N/A'}...")
        logger.info(f"  📌 H1: {h1[:50] if h1 else 'N/A'}...")
        logger.info(f"  📌 Screenshot: {len(screenshot_bytes) / 1024:.1f} KB" if screenshot_bytes else "  📌 Screenshot: N/A")
        
        # Конвертируем скриншот в base64
        screenshot_base64 = parser_service.screenshot_to_base64(screenshot_bytes) if screenshot_bytes else None
        
        # Анализируем сайт через Vision API (скриншот + контекст)
        logger.info("  🤖 Запуск AI анализа...")
        ai_start = time.time()
        
        if screenshot_base64:
            analysis = await openai_service.analyze_website_screenshot(
                screenshot_base64=screenshot_base64,
                url=request.url,
                title=title,
                h1=h1,
                first_paragraph=first_paragraph
            )
        else:
            logger.warning("  ⚠ Скриншот недоступен, fallback на текстовый анализ")
            analysis = await openai_service.analyze_parsed_content(
                title=title,
                h1=h1,
                paragraph=first_paragraph
            )
        
        ai_elapsed = time.time() - ai_start
        logger.info(f"  ✓ AI анализ завершён за {ai_elapsed:.2f} сек")
        
        parsed_content = ParsedContent(
            url=request.url,
            title=title,
            h1=h1,
            first_paragraph=first_paragraph,
            analysis=analysis
        )
        
        # Сохраняем в историю
        logger.info("  💾 Сохранение в историю...")
        history_service.add_entry(
            request_type="parse",
            request_summary=f"URL: {request.url}",
            response_summary=analysis.summary[:100] if analysis.summary else f"Title: {title or 'N/A'}"
        )
        
        total_elapsed = time.time() - total_start
        logger.info(f"  ✅ УСПЕХ: Парсинг и анализ завершён за {total_elapsed:.2f} сек")
        logger.info(f"    - Парсинг: {parse_elapsed:.2f} сек")
        logger.info(f"    - AI анализ: {ai_elapsed:.2f} сек")
        logger.info("=" * 50)
        
        return ParseDemoResponse(
            success=True,
            data=parsed_content
        )
    except Exception as e:
        logger.error(f"  ❌ ОШИБКА: {e}")
        logger.error("=" * 50)
        return ParseDemoResponse(
            success=False,
            error=str(e)
        )

@app.post("/parse_fast", response_model=ParseDemoResponse)
async def parse_fast(request: ParseDemoRequest):
    """
    Быстрый парсинг сайта через HTTP (без скриншота)
    """
    logger.info("=" * 50)
    logger.info("⚡ API: БЫСТРЫЙ ПАРСИНГ")
    logger.info(f"  URL: {request.url}")
    
    try:
        # Парсим
        title, h1, first_paragraph, error = await http_parser_service.parse_url(request.url)
        
        if error:
            logger.error(f"  ❌ Ошибка: {error}")
            logger.info("=" * 50)
            return ParseDemoResponse(success=False, error=error)
        
        # Анализируем через AI
        logger.info("  🤖 Запуск AI анализа...")
        if title or h1 or first_paragraph:
            analysis = await openai_service.analyze_parsed_content(title, h1, first_paragraph)
        else:
            analysis = None
        
        # Сохраняем в историю
        history_service.add_entry(
            request_type="parse",
            request_summary=f"URL: {request.url}",
            response_summary=analysis.summary[:100] if analysis and analysis.summary else f"Title: {title or 'N/A'}"
        )
        
        logger.info("  ✅ УСПЕХ")
        logger.info("=" * 50)
        
        return ParseDemoResponse(
            success=True,
            data=ParsedContent(
                url=request.url,
                title=title,
                h1=h1,
                first_paragraph=first_paragraph,
                analysis=analysis
            )
        )
        
    except Exception as e:
        logger.error(f"  ❌ ОШИБКА: {e}")
        logger.error("=" * 50)
        return ParseDemoResponse(success=False, error=str(e))

@app.get("/history", response_model=HistoryResponse)
async def get_history():
    """
    Получить историю последних 10 запросов
    """
    logger.info("📋 API: Получение истории")
    items = history_service.get_history()
    logger.info(f"  Записей: {len(items)}")
    return HistoryResponse(
        items=items,
        total=len(items)
    )


@app.delete("/history")
async def clear_history():
    """
    Очистить историю запросов
    """
    logger.info("🗑️ API: Очистка истории")
    history_service.clear_history()
    logger.info("  ✓ История очищена")
    return {"success": True, "message": "История очищена"}


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    logger.debug("❤️ Health check")
    return {
        "status": "healthy",
        "service": "Competitor Monitor",
        "version": "1.0.0"
    }

# === PDF Endpoints ===
@app.post("/analyze_pdf", response_model=PDFAnalysisResponse)
async def analyze_pdf(file: UploadFile = File(...)):
    """
    Анализ PDF файла конкурента
    """
    logger.info("=" * 50)
    logger.info("📄 API: АНАЛИЗ PDF")
    logger.info(f"  Имя файла: {file.filename}")
    logger.info(f"  Тип: {file.content_type}")
    
    # Проверяем тип файла
    if file.content_type != "application/pdf":
        logger.warning(f"  ⚠️ Неподдерживаемый тип: {file.content_type}")
        logger.info("=" * 50)
        raise HTTPException(status_code=400, detail="Разрешены только PDF файлы")
    
    try:
        start_time = time.time()
        
        # Читаем файл
        logger.info("  📥 Чтение PDF...")
        content = await file.read()
        file_size_kb = len(content) / 1024
        logger.info(f"  Размер файла: {file_size_kb:.1f} KB")
        
        # Извлекаем текст
        logger.info("  📝 Извлечение текста...")
        text = pdf_service.extract_text_preview(content)
        logger.info(f"  Извлечено символов: {len(text)}")
        
        if not text.strip():
            logger.warning("  ⚠️ Текст не извлечён")
            logger.info("=" * 50)
            return PDFAnalysisResponse(
                success=False,
                error="Не удалось извлечь текст из PDF"
            )
        
        # Анализируем через GPT
        logger.info("  🤖 Анализ через AI...")
        analysis = await openai_service.analyze_text(text)
        
        elapsed = time.time() - start_time
        logger.info(f"  ✓ Анализ завершён за {elapsed:.2f} сек")
        
        # Сохраняем в историю
        history_service.add_entry(
            request_type="pdf",
            request_summary=f"PDF: {file.filename}",
            response_summary=analysis.summary[:200] if analysis.summary else f"Текст: {text[:100]}..."
        )
        
        logger.info("  ✅ УСПЕХ: Анализ PDF завершён")
        logger.info("=" * 50)
        
        return PDFAnalysisResponse(
            success=True,
            extracted_text=text[:500] + ("..." if len(text) > 500 else ""),
            analysis=analysis
        )
        
    except Exception as e:
        logger.error(f"  ❌ ОШИБКА: {e}")
        logger.error("=" * 50)
        return PDFAnalysisResponse(success=False, error=str(e))

# === Report Endpoints ===
@app.post("/generate_report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """
    Генерация отчёта в указанном формате
    """
    logger.info("=" * 50)
    logger.info("📊 API: ГЕНЕРАЦИЯ ОТЧЁТА")
    logger.info(f"  Формат: {request.format}")
    
    try:
        # Восстанавливаем объект анализа
        from backend.models.schemas import CompetitorAnalysis, ImageAnalysis
        
        if request.analysis_data.get('visual_style_score') is not None:
            analysis = ImageAnalysis(**request.analysis_data)
        else:
            analysis = CompetitorAnalysis(**request.analysis_data)
        
        if request.format == "html":
            content = report_service.generate_html(analysis)
            return ReportResponse(
                success=True,
                format="html",
                content=content,
                filename="report.html"
            )
        
        elif request.format == "markdown":
            content = report_service.generate_markdown(analysis)
            return ReportResponse(
                success=True,
                format="markdown",
                content=content,
                filename="report.md"
            )
        
        elif request.format == "pdf":
            pdf_bytes = report_service.generate_pdf(analysis)
            import base64
            content_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            return ReportResponse(
                success=True,
                format="pdf",
                content=content_base64,
                filename="report.pdf"
            )
        
        else:
            logger.warning(f"  ⚠️ Неподдерживаемый формат: {request.format}")
            logger.info("=" * 50)
            return ReportResponse(
                success=False,
                format=request.format,
                error=f"Неподдерживаемый формат: {request.format}"
            )
            
    except ImportError as e:
        logger.error(f"  ❌ Ошибка импорта: {e}")
        logger.error("=" * 50)
        return ReportResponse(success=False, format=request.format, error=str(e))
    except Exception as e:
        logger.error(f"  ❌ ОШИБКА: {e}")
        logger.error("=" * 50)
        return ReportResponse(success=False, format=request.format, error=str(e))

# === Visualization Endpoints ===
@app.post("/visualize", response_model=VisualizationResponse)
async def visualize(request: VisualizationRequest):
    """
    Генерация визуализации (графиков)
    """
    logger.info("=" * 50)
    logger.info("📈 API: ВИЗУАЛИЗАЦИЯ")
    logger.info(f"  Тип графика: {request.chart_type}")
    
    try:
        from backend.models.schemas import CompetitorAnalysis, ImageAnalysis
        
        # Восстанавливаем объект анализа
        if request.analysis_data.get('visual_style_score') is not None:
            analysis = ImageAnalysis(**request.analysis_data)
        else:
            analysis = CompetitorAnalysis(**request.analysis_data)
        
        if request.chart_type == "radar":
            if not isinstance(analysis, CompetitorAnalysis):
                logger.warning("  ⚠️ Radar только для текстового анализа")
                return VisualizationResponse(
                    success=False,
                    chart_type="radar",
                    error="Radar chart доступен только для текстового анализа"
                )
            
            image_base64 = viz_service.generate_radar_chart(
                strengths=analysis.strengths,
                weaknesses=analysis.weaknesses,
                unique_offers=analysis.unique_offers,
                recommendations=analysis.recommendations,
                title="Анализ конкурента"
            )
        
        elif request.chart_type == "bar":
            if not isinstance(analysis, CompetitorAnalysis):
                logger.warning("  ⚠️ Bar только для текстового анализа")
                return VisualizationResponse(
                    success=False,
                    chart_type="bar",
                    error="Bar chart доступен только для текстового анализа"
                )
            
            image_base64 = viz_service.generate_comparison_bar_chart(
                analysis=analysis,
                title="Сравнение характеристик"
            )
        
        elif request.chart_type == "score":
            if not isinstance(analysis, ImageAnalysis):
                logger.warning("  ⚠️ Score только для анализа изображений")
                return VisualizationResponse(
                    success=False,
                    chart_type="score",
                    error="Score chart доступен только для анализа изображений"
                )
            
            image_base64 = viz_service.generate_visual_score_chart(
                score=analysis.visual_style_score
            )
        
        else:
            logger.warning(f"  ⚠️ Неподдерживаемый тип: {request.chart_type}")
            logger.info("=" * 50)
            return VisualizationResponse(
                success=False,
                chart_type=request.chart_type,
                error=f"Неподдерживаемый тип графика: {request.chart_type}"
            )
        
        if not image_base64:
            logger.warning("  ⚠️ График не сгенерирован")
            logger.info("=" * 50)
            return VisualizationResponse(
                success=False,
                chart_type=request.chart_type,
                error="Не удалось сгенерировать график"
            )
        
        logger.info("  ✅ УСПЕХ: Визуализация создана")
        logger.info("=" * 50)
        
        return VisualizationResponse(
            success=True,
            chart_type=request.chart_type,
            image_base64=image_base64
        )
        
    except Exception as e:
        logger.error(f"  ❌ ОШИБКА: {e}")
        logger.error("=" * 50)
        return VisualizationResponse(success=False, chart_type=request.chart_type, error=str(e))

# Статические файлы для фронтенда
app.mount("/static", StaticFiles(directory="frontend"), name="static")
logger.info("Статические файлы подключены: /static -> frontend/")

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
