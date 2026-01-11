"""
Быстрый парсинг через HTTP (без Selenium)
"""
import logging
from typing import Optional, Tuple
from bs4 import BeautifulSoup
from backend.config import settings

logger = logging.getLogger("competitor_monitor.http_parser")

class HTTPParserService:
    """Быстрый HTTP парсинг без браузера"""
    
    def __init__(self):
        logger.info("=" * 50)
        logger.info("Инициализация HTTP Parser сервиса")
        logger.info("HTTP Parser сервис инициализирован ✓")
        logger.info("=" * 50)
    
    async def parse_url(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Быстрый парсинг URL через HTTP
        
        Returns:
            title, h1, first_paragraph, error
        """
        logger.info("=" * 50)
        logger.info(f"🌐 HTTP ПАРСИНГ: {url}")
        
        try:
            import httpx
            import asyncio
            
            logger.info("  📥 Загрузка страницы...")
            
            # Быстрый HTTP запрос
            response = await asyncio.wait_for(
                httpx.AsyncClient().aget(url, timeout=15.0, follow_redirects=True),
                timeout=15.0
            )
            
            logger.info(f"  ✓ Загружено: {len(response.text)} символов, статус: {response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"  ⚠️ Необычный статус: {response.status_code}")
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Title
            title = soup.title.string.strip() if soup.title and soup.title.string else None
            logger.info(f"  📌 Title: {title[:60] if title else 'N/A'}...")
            
            # H1
            h1 = None
            h1_tag = soup.find('h1')
            if h1_tag:
                h1 = h1_tag.get_text(strip=True)
                if len(h1) > 500:
                    h1 = h1[:500]
            logger.info(f"  📌 H1: {h1[:60] if h1 else 'N/A'}...")
            
            # Первый абзац
            first_paragraph = None
            p_tags = soup.find_all('p')
            for p in p_tags:
                text = p.get_text(strip=True)
                if len(text) > 50:
                    first_paragraph = text[:500]
                    logger.info(f"  📌 Первый абзац: {first_paragraph[:60]}...")
                    break
            
            logger.info("  ✅ HTTP парсинг завершён")
            logger.info("=" * 50)
            
            return title, h1, first_paragraph, None
            
        except asyncio.TimeoutError:
            logger.error("  ✗ Таймаут загрузки")
            logger.error("=" * 50)
            return None, None, None, "Превышено время ожидания загрузки страницы"
            
        except Exception as e:
            logger.error(f"  ✗ Ошибка: {e}")
            logger.error("=" * 50)
            return None, None, None, f"Ошибка при загрузке страницы: {str(e)[:100]}"


# Глобальный экземпляр
http_parser_service = HTTPParserService()