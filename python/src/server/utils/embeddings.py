"""
Embedding generation utilities for semantic search.
Handles vector generation for tasks, projects, sessions, and events.

This version wraps the core embedding service to provide provider-agnostic
embedding generation using OpenAI, Google, or Ollama.
"""
from typing import Optional
import os

from ..services.embeddings.embedding_service import create_embedding, create_embeddings_batch
from ..config.logfire_config import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings using the configured provider.

    This service provides a centralized way to generate embeddings for:
    - Tasks (title + description)
    - Projects (title + description + features)
    - Sessions (summary + key events)
    - Events (event_type + event_data)
    - Arbitrary text
    """

    def __init__(self):
        """Initialize the embedding service."""
        # Provider settings are handled by the core embedding service
        pass

    async def generate_embedding(self, text: str) -> Optional[list[float]]:
        """
        Generate embedding vector for arbitrary text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector, or None if text is empty/invalid
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return None

        try:
            return await create_embedding(text)
        except Exception as e:
            logger.warning(f"Embedding generation failed: {str(e)}")
            return None

    async def generate_task_embedding(self, task: dict) -> Optional[list[float]]:
        """
        Generate embedding for a task.
        """
        title = task.get('title', '')
        description = task.get('description', '')
        text = f"{title}. {description}".strip()

        if not text or text == '.':
            return None

        return await self.generate_embedding(text)

    async def generate_project_embedding(self, project: dict) -> Optional[list[float]]:
        """
        Generate embedding for a project.
        """
        title = project.get('title', '')
        description = project.get('description', '')
        features = project.get('features', [])

        features_text = ' '.join(features) if features else ''
        text = f"{title}. {description}. {features_text}".strip()

        if not text or text == '.':
            return None

        return await self.generate_embedding(text)

    async def generate_session_embedding(self, session: dict) -> Optional[list[float]]:
        """
        Generate embedding for a session.
        """
        summary = session.get('summary', '')
        metadata = session.get('metadata', {})

        key_events = metadata.get('key_events', [])
        decisions = metadata.get('decisions', [])
        outcomes = metadata.get('outcomes', [])

        events_text = ' '.join(key_events) if key_events else ''
        decisions_text = ' '.join(decisions) if decisions else ''
        outcomes_text = ' '.join(outcomes) if outcomes else ''

        text = f"{summary}. {events_text}. {decisions_text}. {outcomes_text}".strip()

        if not text or text == '.':
            return None

        return await self.generate_embedding(text)

    async def generate_event_embedding(self, event: dict) -> Optional[list[float]]:
        """
        Generate embedding for a session event.
        """
        event_type = event.get('event_type', '')
        event_data = event.get('event_data', {})

        if isinstance(event_data, dict):
            event_data_text = ' '.join([
                f"{k}: {v}" for k, v in event_data.items()
                if v is not None
            ])
        else:
            event_data_text = str(event_data)

        text = f"{event_type}. {event_data_text}".strip()

        if not text or text == '.':
            return None

        return await self.generate_embedding(text)

    async def batch_generate_embeddings(
        self,
        texts: list[str]
    ) -> list[Optional[list[float]]]:
        """
        Generate embeddings for multiple texts.
        """
        if not texts:
            return []

        try:
            result = await create_embeddings_batch(texts)
            # Map result back to original order, filling in None for failures
            # This is a bit simplified compared to the original but should work
            return [res if res else None for res in result.embeddings]
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            return [None] * len(texts)


# Singleton instance for convenience
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create the singleton EmbeddingService instance.
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
