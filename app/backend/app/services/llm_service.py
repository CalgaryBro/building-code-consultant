"""
LLM Service Client - Connects to the containerized LLM service.

This service calls the separate LLM Docker container that runs the
LiquidAI LFM2.5-1.2B-Instruct model with dedicated resources.

The LLM container provides:
- Resource isolation (CPU/memory limits)
- Prometheus metrics for monitoring
- Health checks
- Model caching
"""
import os
import logging
from typing import Optional, Dict, Any
import httpx
from functools import lru_cache

logger = logging.getLogger(__name__)

# LLM Service configuration
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8081")
LLM_SERVICE_TIMEOUT = int(os.getenv("LLM_SERVICE_TIMEOUT", "120"))  # seconds


class LLMServiceClient:
    """Client for the containerized LLM service."""

    def __init__(self, base_url: str = LLM_SERVICE_URL):
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=httpx.Timeout(LLM_SERVICE_TIMEOUT, connect=10.0),
            )
        return self._client

    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def is_healthy(self) -> bool:
        """Check if the LLM service is healthy."""
        try:
            response = self._get_client().get("/health")
            if response.status_code == 200:
                data = response.json()
                return data.get("model_loaded", False)
            return False
        except Exception as e:
            logger.warning(f"LLM service health check failed: {e}")
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status from the LLM service."""
        try:
            response = self._get_client().get("/health")
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "model_loaded": False}
        except Exception as e:
            logger.warning(f"Failed to get LLM service health: {e}")
            return {"status": "unavailable", "model_loaded": False, "error": str(e)}

    def get_resource_stats(self) -> Dict[str, Any]:
        """Get resource usage statistics from the LLM service."""
        try:
            response = self._get_client().get("/stats")
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.warning(f"Failed to get LLM service stats: {e}")
            return {"error": str(e)}

    def generate_response(
        self,
        question: str,
        context: str,
        max_new_tokens: int = 512,
        temperature: float = 0.1,
    ) -> Optional[str]:
        """
        Generate a response to a question using the LLM service.

        Args:
            question: The user's question
            context: Relevant context from building codes/standards
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (lower = more focused)

        Returns:
            Generated response or None if service unavailable
        """
        try:
            response = self._get_client().post(
                "/generate",
                json={
                    "question": question,
                    "context": context,
                    "max_new_tokens": max_new_tokens,
                    "temperature": temperature,
                },
            )

            if response.status_code == 200:
                data = response.json()
                logger.info(
                    f"LLM response generated: {data.get('tokens_generated', 0)} tokens, "
                    f"{data.get('latency_ms', 0):.0f}ms latency"
                )
                return data.get("response")
            elif response.status_code == 503:
                logger.warning("LLM service model not loaded yet")
                return None
            else:
                logger.error(f"LLM service error: {response.status_code} - {response.text}")
                return None

        except httpx.TimeoutException:
            logger.error("LLM service request timed out")
            return None
        except httpx.ConnectError:
            logger.warning("Could not connect to LLM service")
            return None
        except Exception as e:
            logger.error(f"Error calling LLM service: {e}")
            return None

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        try:
            response = self._get_client().get("/model-info")
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.warning(f"Failed to get model info: {e}")
            return {"error": str(e)}


# Backward-compatible LLMService class
class LLMService:
    """
    Service for generating AI responses using the containerized LLM service.

    This is a wrapper around LLMServiceClient for backward compatibility
    with existing code that uses LLMService.
    """

    SYSTEM_PROMPT = """You are a knowledgeable assistant specializing in the Alberta Building Code, Calgary building regulations, STANDATA bulletins, and construction permit requirements.

Your role is to:
1. Answer questions about building codes accurately and concisely
2. Cite specific code sections when available
3. Explain complex requirements in plain language
4. Note when questions require professional consultation

Always be helpful but remind users to verify information with official sources and consult licensed professionals for specific projects."""

    def __init__(self):
        self._client = LLMServiceClient()

    def _ensure_model_loaded(self) -> bool:
        """Check if the LLM service is available and model is loaded."""
        return self._client.is_healthy()

    def generate_response(
        self,
        question: str,
        context: str,
        max_new_tokens: int = 512,
        temperature: float = 0.1,
    ) -> Optional[str]:
        """
        Generate a response to a question using the provided context.

        Args:
            question: The user's question
            context: Relevant context from building codes/standards
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (lower = more focused)

        Returns:
            Generated response or None if service unavailable
        """
        return self._client.generate_response(
            question=question,
            context=context,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        info = self._client.get_model_info()
        stats = self._client.get_resource_stats()

        return {
            **info,
            "service_url": LLM_SERVICE_URL,
            "resource_stats": stats,
        }


def is_model_available() -> bool:
    """Check if the LLM service is available (without loading it)."""
    try:
        client = LLMServiceClient()
        health = client.get_health_status()
        return health.get("status") in ["healthy", "loading"]
    except Exception:
        return False


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
