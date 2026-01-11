"""
Сервис для извлечения текста из PDF файлов
"""
import logging
from typing import Optional
from PyPDF2 import PdfReader
from backend.config import settings
from backend.models.schemas import CompetitorAnalysis

logger = logging.getLogger("competitor_monitor.pdf")

class PDFService:
    """Извлечение текста из PDF файлов"""
    
    def __init__(self):
        logger.info("=" * 50)
        logger.info("Инициализация PDF сервиса")
        logger.info("PDF сервис инициализирован ✓")
        logger.info("=" * 50)
    
    def extract_text(self, file_content: bytes) -> str:
        """
        Извлечь текст из PDF файла
        
        Args:
            file_content: Содержимое PDF файла в байтах
            
        Returns:
            Извлечённый текст
        """
        logger.info("=" * 50)
        logger.info("📄 ИЗВЛЕЧЕНИЕ ТЕКСТА ИЗ PDF")
        
        try:
            # Читаем PDF из байтов
            import io
            pdf_stream = io.BytesIO(file_content)
            reader = PdfReader(pdf_stream)
            
            num_pages = len(reader.pages)
            logger.info(f"  Страниц в PDF: {num_pages}")
            
            full_text = []
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    text = text.strip()
                    if text:
                        full_text.append(text)
                        logger.debug(f"  Страница {i+1}: {len(text)} символов")
            
            combined_text = "\n\n".join(full_text)
            
            logger.info(f"  ✓ Извлечено символов: {len(combined_text)}")
            logger.info(f"  ✓ Непустых страниц: {len(full_text)}")
            logger.info("=" * 50)
            
            return combined_text
            
        except Exception as e:
            logger.error(f"  ✗ Ошибка при извлечении текста: {e}")
            logger.error("=" * 50)
            raise
    
    def extract_text_preview(self, file_content: bytes, max_chars: int = 5000) -> str:
        """
        Извлечь превью текста из PDF (для анализа)
        
        Args:
            file_content: Содержимое PDF файла
            max_chars: Максимум символов для анализа
            
        Returns:
            Текст превью
        """
        full_text = self.extract_text(file_content)
        
        if len(full_text) > max_chars:
            logger.info(f"  📝 Текст обрезан: {len(full_text)} -> {max_chars} символов")
            return full_text[:max_chars]
        
        return full_text

# Глобальный экземпляр
pdf_service = PDFService()