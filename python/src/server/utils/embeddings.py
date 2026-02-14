"""
Embedding generation utilities for semantic search.
Handles vector generation for tasks, projects, sessions, and events.

This service uses OpenAI's text-embedding-3-small model for cost-effective
embedding generation across all Archon memory layers.
"""
from typing import Optional
from openai import AsyncOpenAI
import os

# Use Archon's standard logging
from ..config.logfire_config import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings using OpenAI's embedding model.

    This service provides a centralized way to generate embeddings for:
    - Tasks (title + description)
    - Projects (title + description + features)
    - Sessions (summary + key events)
    - Events (event_type + event_data)
    - Arbitrary text

    Uses text-embedding-3-small (1536 dimensions) for cost-effectiveness.
    """

    def __init__(self):
        """Initialize the embedding service with OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set - embeddings will fail")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"  # 1536 dimensions, cost-effective
        self.max_input_length = 8000  # Model limit

    async def generate_embedding(self, text: str) -> Optional[list[float]]:
        """
        Generate embedding vector for arbitrary text.

        Args:
            text: Input text to embed (will be truncated to 8000 chars)

        Returns:
            1536-dimensional embedding vector, or None if text is empty/invalid

        Raises:
            Exception: If OpenAI API call fails
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding generation")
            return None

        try:
            # Truncate to model limit
            truncated_text = text[:self.max_input_length]

            if len(text) > self.max_input_length:
                logger.info(
                    f"Text truncated from {len(text)} to {self.max_input_length} chars"
                )

            # Generate embedding
            response = await self.client.embeddings.create(
                model=self.model,
                input=truncated_text
            )

            embedding = response.data[0].embedding

            logger.debug(
                f"Generated embedding: {len(embedding)} dimensions, "
                f"input length: {len(truncated_text)} chars"
            )

            return embedding

        except Exception as e:
            logger.warning(f"Embedding generation failed: {str(e)}")
            logger.debug("Embedding failure details", exc_info=True)
            return None

    async def generate_task_embedding(self, task: dict) -> Optional[list[float]]:
        """
        Generate embedding for a task.

        Combines title and description for comprehensive task representation.

        Args:
            task: Task dictionary with 'title' and optionally 'description'

        Returns:
            1536-dimensional embedding vector

        Example:
            task = {"title": "Implement sessions", "description": "Add session tracking..."}
            embedding = await service.generate_task_embedding(task)
        """
        title = task.get('title', '')
        description = task.get('description', '')

        # Combine title and description with title weighted more
        text = f"{title}. {description}".strip()

        if not text or text == '.':
            logger.warning(f"Task has no content for embedding: {task.get('id')}")
            return None

        logger.debug(f"Generating task embedding: {title[:50]}...")
        return await self.generate_embedding(text)

    async def generate_project_embedding(self, project: dict) -> Optional[list[float]]:
        """
        Generate embedding for a project.

        Combines title, description, and features for comprehensive representation.

        Args:
            project: Project dictionary with 'title', 'description', and 'features'

        Returns:
            1536-dimensional embedding vector

        Example:
            project = {
                "title": "Shared Memory System",
                "description": "Implement shared memory...",
                "features": ["Phase 1: MCP", "Phase 2: Sessions"]
            }
            embedding = await service.generate_project_embedding(project)
        """
        title = project.get('title', '')
        description = project.get('description', '')
        features = project.get('features', [])

        # Combine all text
        features_text = ' '.join(features) if features else ''
        text = f"{title}. {description}. {features_text}".strip()

        if not text or text == '.':
            logger.warning(f"Project has no content for embedding: {project.get('id')}")
            return None

        logger.debug(f"Generating project embedding: {title[:50]}...")
        return await self.generate_embedding(text)

    async def generate_session_embedding(self, session: dict) -> Optional[list[float]]:
        """
        Generate embedding for a session.

        Combines summary and key events from metadata for comprehensive representation.

        Args:
            session: Session dictionary with 'summary' and optionally 'metadata'

        Returns:
            1536-dimensional embedding vector

        Example:
            session = {
                "summary": "Completed Phase 2 Day 1...",
                "metadata": {
                    "key_events": ["migration_created", "tables_created"],
                    "decisions": ["use pgvector"],
                    "outcomes": ["database ready"]
                }
            }
            embedding = await service.generate_session_embedding(session)
        """
        summary = session.get('summary', '')
        metadata = session.get('metadata', {})

        # Extract key information from metadata
        key_events = metadata.get('key_events', [])
        decisions = metadata.get('decisions', [])
        outcomes = metadata.get('outcomes', [])

        # Combine all text
        events_text = ' '.join(key_events) if key_events else ''
        decisions_text = ' '.join(decisions) if decisions else ''
        outcomes_text = ' '.join(outcomes) if outcomes else ''

        text = f"{summary}. {events_text}. {decisions_text}. {outcomes_text}".strip()

        if not text or text == '.':
            logger.warning(f"Session has no content for embedding: {session.get('id')}")
            return None

        logger.debug(f"Generating session embedding: {summary[:50]}...")
        return await self.generate_embedding(text)

    async def generate_event_embedding(self, event: dict) -> Optional[list[float]]:
        """
        Generate embedding for a session event.

        Combines event_type and stringified event_data.

        Args:
            event: Event dictionary with 'event_type' and 'event_data'

        Returns:
            1536-dimensional embedding vector

        Example:
            event = {
                "event_type": "task_created",
                "event_data": {"task_id": "123", "title": "New task"}
            }
            embedding = await service.generate_event_embedding(event)
        """
        event_type = event.get('event_type', '')
        event_data = event.get('event_data', {})

        # Convert event_data to readable text
        if isinstance(event_data, dict):
            event_data_text = ' '.join([
                f"{k}: {v}" for k, v in event_data.items()
                if v is not None
            ])
        else:
            event_data_text = str(event_data)

        text = f"{event_type}. {event_data_text}".strip()

        if not text or text == '.':
            logger.warning(f"Event has no content for embedding: {event.get('id')}")
            return None

        logger.debug(f"Generating event embedding: {event_type}")
        return await self.generate_embedding(text)

    async def batch_generate_embeddings(
        self,
        texts: list[str]
    ) -> list[Optional[list[float]]]:
        """
        Generate embeddings for multiple texts in a single API call.

        More efficient than individual calls when processing many items.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (same order as input)

        Note:
            Returns None for empty/invalid texts in the list
        """
        if not texts:
            return []

        try:
            # Filter out empty texts but remember their positions
            valid_texts = []
            text_indices = []

            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_texts.append(text[:self.max_input_length])
                    text_indices.append(i)

            if not valid_texts:
                logger.warning("No valid texts to embed in batch")
                return [None] * len(texts)

            # Generate embeddings for all valid texts
            response = await self.client.embeddings.create(
                model=self.model,
                input=valid_texts
            )

            # Build result list with None for invalid texts
            results = [None] * len(texts)
            for idx, embedding_data in zip(text_indices, response.data):
                results[idx] = embedding_data.embedding

            logger.info(
                f"Batch generated {len(valid_texts)} embeddings "
                f"({len(texts) - len(valid_texts)} skipped)"
            )

            return results

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}", exc_info=True)
            raise


# Singleton instance for convenience
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create the singleton EmbeddingService instance.

    Returns:
        Shared EmbeddingService instance

    Example:
        service = get_embedding_service()
        embedding = await service.generate_embedding("some text")
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
