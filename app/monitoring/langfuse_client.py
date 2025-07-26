import os
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class LLMRequest:
    """Структура для LLM запроса"""
    model: str
    messages: List[Dict[str, str]]
    user_id: str
    request_id: str
    start_time: float
    stream: bool = False

@dataclass
class LLMResponse:
    """Структура для LLM ответа"""
    request_id: str
    model: str
    completion_tokens: Optional[int] = None
    prompt_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost: Optional[float] = None
    end_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None

class LangfuseClient:
    """Клиент для интеграции с Langfuse"""
    
    def __init__(self, langfuse_secret_key: Optional[str] = None):
        self.langfuse_secret_key = langfuse_secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        self.enabled = bool(self.langfuse_secret_key)
        
        if self.enabled:
            try:
                from langfuse import Langfuse
                self.client = Langfuse(
                    secret_key=self.langfuse_secret_key,
                    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
                )
                logger.info("Langfuse client initialized successfully")
            except ImportError:
                logger.warning("Langfuse not installed, monitoring disabled")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Langfuse client: {e}")
                self.enabled = False
        else:
            logger.info("Langfuse secret key not provided, monitoring disabled")
            self.enabled = False
    
    def start_generation(
        self,
        request_id: str,
        model: str,
        messages: List[Dict[str, str]],
        user_id: str,
        stream: bool = False
    ) -> Optional[str]:
        """Начинает отслеживание LLM генерации"""
        if not self.enabled:
            return None
        
        try:
            # Создаем trace для отслеживания
            trace = self.client.trace(
                id=request_id,
                name=f"LLM Generation - {model}",
                user_id=user_id,
                metadata={
                    "model": model,
                    "stream": stream,
                    "message_count": len(messages)
                }
            )
            
            # Создаем generation span
            generation = trace.generation(
                name=f"Chat Completion - {model}",
                model=model,
                model_parameters={
                    "stream": stream,
                    "temperature": 0.7,  # Default, можно сделать настраиваемым
                    "max_tokens": 1000   # Default, можно сделать настраиваемым
                },
                input=messages,
                start_time=datetime.now()
            )
            
            return generation.id
            
        except Exception as e:
            logger.error(f"Failed to start Langfuse generation: {e}")
            return None
    
    def end_generation(
        self,
        generation_id: str,
        output: Optional[str] = None,
        usage: Optional[Dict[str, int]] = None,
        cost: Optional[float] = None,
        error: Optional[str] = None
    ):
        """Завершает отслеживание LLM генерации"""
        if not self.enabled or not generation_id:
            return
        
        try:
            # Получаем generation span
            generation = self.client.generation(generation_id)
            
            # Обновляем с результатами
            update_data = {
                "end_time": datetime.now()
            }
            
            if output:
                update_data["output"] = output
            
            if usage:
                update_data["usage"] = usage
            
            if cost:
                update_data["cost"] = cost
            
            if error:
                update_data["level"] = "ERROR"
                update_data["status_message"] = error
            
            generation.update(**update_data)
            
        except Exception as e:
            logger.error(f"Failed to end Langfuse generation: {e}")
    
    def log_score(
        self,
        request_id: str,
        score_name: str,
        score_value: float,
        comment: Optional[str] = None
    ):
        """Логирует score для запроса"""
        if not self.enabled:
            return
        
        try:
            trace = self.client.trace(request_id)
            trace.score(
                name=score_name,
                value=score_value,
                comment=comment
            )
        except Exception as e:
            logger.error(f"Failed to log Langfuse score: {e}")
    
    def log_span(
        self,
        request_id: str,
        name: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Логирует span для отслеживания операций"""
        if not self.enabled:
            return
        
        try:
            trace = self.client.trace(request_id)
            span = trace.span(
                name=name,
                input=input_data,
                output=output_data,
                metadata=metadata
            )
            return span.id
        except Exception as e:
            logger.error(f"Failed to log Langfuse span: {e}")
            return None
    
    def end_span(self, span_id: str, output_data: Optional[Dict[str, Any]] = None):
        """Завершает span"""
        if not self.enabled or not span_id:
            return
        
        try:
            span = self.client.span(span_id)
            span.end(output=output_data)
        except Exception as e:
            logger.error(f"Failed to end Langfuse span: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья Langfuse клиента"""
        return {
            "enabled": self.enabled,
            "status": "healthy" if self.enabled else "disabled",
            "error": None
        }

# Global Langfuse client instance
langfuse_client = LangfuseClient() 