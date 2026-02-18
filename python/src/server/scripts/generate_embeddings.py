"""
Generate embeddings for existing database records.

This script generates vector embeddings for:
- Sessions (archon_sessions)
- Session events (archon_session_events)
- Conversation messages (conversation_history)

Usage:
    python -m src.server.scripts.generate_embeddings [--batch-size 10] [--dry-run]
"""
import asyncio
import argparse
from typing import Optional
from datetime import datetime

from src.server.utils import get_supabase_client
from src.server.config.logfire_config import get_logger
from src.server.utils.embeddings import get_embedding_service
from src.server.services.memory_service import get_memory_service

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for existing database records."""

    def __init__(self, batch_size: int = 10, dry_run: bool = False):
        """
        Initialize embedding generator.

        Args:
            batch_size: Number of records to process in each batch
            dry_run: If True, don't actually update the database
        """
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.supabase = get_supabase_client()
        self.embedding_service = get_embedding_service()
        self.memory_service = get_memory_service()

        # Statistics
        self.stats = {
            "sessions": {"total": 0, "processed": 0, "skipped": 0, "failed": 0},
            "events": {"total": 0, "processed": 0, "skipped": 0, "failed": 0},
            "conversations": {"total": 0, "processed": 0, "skipped": 0, "failed": 0},
        }

    async def generate_session_embeddings(self) -> None:
        """Generate embeddings for sessions without embeddings."""
        logger.info("Generating embeddings for sessions...")

        # Get all sessions without embeddings
        response = self.supabase.table("archon_sessions").select("*").is_("embedding", "null").execute()

        sessions = response.data or []
        self.stats["sessions"]["total"] = len(sessions)

        logger.info(f"Found {len(sessions)} sessions without embeddings")

        for i in range(0, len(sessions), self.batch_size):
            batch = sessions[i : i + self.batch_size]
            await self._process_session_batch(batch)

        logger.info(
            f"Sessions: {self.stats['sessions']['processed']} processed, "
            f"{self.stats['sessions']['skipped']} skipped, "
            f"{self.stats['sessions']['failed']} failed"
        )

    async def _process_session_batch(self, sessions: list[dict]) -> None:
        """Process a batch of sessions."""
        for session in sessions:
            session_id = session["id"]

            try:
                # Generate embedding text from session
                agent = session.get("agent", "")
                summary = session.get("summary", "")
                context = session.get("context", {})

                # Construct meaningful text for embedding
                context_text = ""
                if isinstance(context, dict):
                    context_text = " ".join([f"{k}: {v}" for k, v in context.items() if v])

                embedding_text = f"Agent {agent} session. {summary} {context_text}".strip()

                if not embedding_text or embedding_text == f"Agent {agent} session.":
                    logger.warning(f"Skipping session {session_id}: no meaningful text")
                    self.stats["sessions"]["skipped"] += 1
                    continue

                # Generate embedding using Ollama (local, no API key required)
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "http://host.docker.internal:11434/api/embeddings",
                        json={"model": "nomic-embed-text", "prompt": embedding_text},
                        timeout=30.0
                    )
                    response.raise_for_status()
                    embedding = response.json()["embedding"]
                    # Pad to 1536 dimensions (nomic-embed-text is 768-dim)
                    if len(embedding) < 1536:
                        embedding = embedding + [0.0] * (1536 - len(embedding))

                if not embedding:
                    logger.warning(f"Failed to generate embedding for session {session_id}")
                    self.stats["sessions"]["failed"] += 1
                    continue

                # Update session with embedding
                if not self.dry_run:
                    self.supabase.table("archon_sessions").update({"embedding": embedding}).eq(
                        "id", session_id
                    ).execute()

                self.stats["sessions"]["processed"] += 1
                logger.debug(f"Generated embedding for session {session_id}")

            except Exception as e:
                logger.error(f"Error processing session {session_id}: {e}", exc_info=True)
                self.stats["sessions"]["failed"] += 1

    async def generate_event_embeddings(self) -> None:
        """Generate embeddings for session events without embeddings."""
        logger.info("Generating embeddings for session events...")

        # Get all events without embeddings
        response = (
            self.supabase.table("archon_session_events").select("*").is_("embedding", "null").execute()
        )

        events = response.data or []
        self.stats["events"]["total"] = len(events)

        logger.info(f"Found {len(events)} events without embeddings")

        for i in range(0, len(events), self.batch_size):
            batch = events[i : i + self.batch_size]
            await self._process_event_batch(batch)

        logger.info(
            f"Events: {self.stats['events']['processed']} processed, "
            f"{self.stats['events']['skipped']} skipped, "
            f"{self.stats['events']['failed']} failed"
        )

    async def _process_event_batch(self, events: list[dict]) -> None:
        """Process a batch of events."""
        for event in events:
            event_id = event["id"]

            try:
                # Generate embedding for event using OpenAI
                event_type = event.get("event_type", "")
                event_data = event.get("event_data", {})

                if isinstance(event_data, dict):
                    event_data_text = " ".join([f"{k}: {v}" for k, v in event_data.items() if v])
                else:
                    event_data_text = str(event_data)

                embedding_text = f"{event_type}. {event_data_text}".strip()

                # Generate embedding using Ollama
                import httpx
                if embedding_text and embedding_text != ".":
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            "http://host.docker.internal:11434/api/embeddings",
                            json={"model": "nomic-embed-text", "prompt": embedding_text},
                            timeout=30.0
                        )
                        response.raise_for_status()
                        embedding = response.json()["embedding"]
                        # Pad to 1536 dimensions (nomic-embed-text is 768-dim)
                        if len(embedding) < 1536:
                            embedding = embedding + [0.0] * (1536 - len(embedding))
                else:
                    embedding = None

                if not embedding:
                    logger.warning(f"Failed to generate embedding for event {event_id}")
                    self.stats["events"]["failed"] += 1
                    continue

                # Update event with embedding
                if not self.dry_run:
                    self.supabase.table("archon_session_events").update(
                        {"embedding": embedding}
                    ).eq("id", event_id).execute()

                self.stats["events"]["processed"] += 1
                logger.debug(f"Generated embedding for event {event_id}")

            except Exception as e:
                logger.error(f"Error processing event {event_id}: {e}", exc_info=True)
                self.stats["events"]["failed"] += 1

    async def generate_conversation_embeddings(self) -> None:
        """Generate embeddings for conversation messages without embeddings."""
        logger.info("Generating embeddings for conversation messages...")

        # Get all conversations without embeddings
        response = (
            self.supabase.table("conversation_history").select("*").is_("embedding", "null").execute()
        )

        conversations = response.data or []
        self.stats["conversations"]["total"] = len(conversations)

        logger.info(f"Found {len(conversations)} conversation messages without embeddings")

        for i in range(0, len(conversations), self.batch_size):
            batch = conversations[i : i + self.batch_size]
            await self._process_conversation_batch(batch)

        logger.info(
            f"Conversations: {self.stats['conversations']['processed']} processed, "
            f"{self.stats['conversations']['skipped']} skipped, "
            f"{self.stats['conversations']['failed']} failed"
        )

    async def _process_conversation_batch(self, conversations: list[dict]) -> None:
        """Process a batch of conversation messages."""
        for conversation in conversations:
            conv_id = conversation["id"]

            try:
                role = conversation.get("role", "")
                message = conversation.get("message", "")
                message_type = conversation.get("type")

                # Create embedding-optimized text (same as MemoryService)
                embedding_text = f"{role}: {message}"
                if message_type:
                    embedding_text = f"[{message_type}] {embedding_text}"

                # Generate embedding using Ollama (local, no API key required)
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "http://host.docker.internal:11434/api/embeddings",
                        json={"model": "nomic-embed-text", "prompt": embedding_text},
                        timeout=30.0
                    )
                    response.raise_for_status()
                    embedding = response.json()["embedding"]
                    # Pad to 1536 dimensions (nomic-embed-text is 768-dim)
                    if len(embedding) < 1536:
                        embedding = embedding + [0.0] * (1536 - len(embedding))

                if not embedding:
                    logger.warning(f"Failed to generate embedding for conversation {conv_id}")
                    self.stats["conversations"]["failed"] += 1
                    continue

                # Update conversation with embedding
                if not self.dry_run:
                    self.supabase.table("conversation_history").update(
                        {"embedding": embedding}
                    ).eq("id", conv_id).execute()

                self.stats["conversations"]["processed"] += 1
                logger.debug(f"Generated embedding for conversation {conv_id}")

            except Exception as e:
                logger.error(f"Error processing conversation {conv_id}: {e}", exc_info=True)
                self.stats["conversations"]["failed"] += 1

    async def run(self) -> dict:
        """
        Run the embedding generation process.

        Returns:
            Statistics dictionary with processing results
        """
        start_time = datetime.now()

        if self.dry_run:
            logger.info("DRY RUN MODE: No database updates will be performed")

        logger.info("Starting embedding generation process...")

        # Generate embeddings for all record types
        await self.generate_session_embeddings()
        await self.generate_event_embeddings()
        await self.generate_conversation_embeddings()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Calculate totals
        total_processed = sum(s["processed"] for s in self.stats.values())
        total_failed = sum(s["failed"] for s in self.stats.values())
        total_skipped = sum(s["skipped"] for s in self.stats.values())

        logger.info(
            f"\nEmbedding generation complete in {duration:.2f}s:\n"
            f"  Processed: {total_processed}\n"
            f"  Failed: {total_failed}\n"
            f"  Skipped: {total_skipped}"
        )

        return {
            "stats": self.stats,
            "duration_seconds": duration,
            "dry_run": self.dry_run,
        }


async def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Generate embeddings for existing database records"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of records to process in each batch (default: 10)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Don't actually update the database"
    )

    args = parser.parse_args()

    generator = EmbeddingGenerator(batch_size=args.batch_size, dry_run=args.dry_run)

    try:
        results = await generator.run()

        if args.dry_run:
            print("\n✅ DRY RUN COMPLETE - No changes made to database")
        else:
            print("\n✅ EMBEDDING GENERATION COMPLETE")

        print(f"\nResults:")
        print(f"  Duration: {results['duration_seconds']:.2f}s")
        print(f"\n  Sessions:")
        print(f"    Total: {results['stats']['sessions']['total']}")
        print(f"    Processed: {results['stats']['sessions']['processed']}")
        print(f"    Failed: {results['stats']['sessions']['failed']}")
        print(f"    Skipped: {results['stats']['sessions']['skipped']}")
        print(f"\n  Events:")
        print(f"    Total: {results['stats']['events']['total']}")
        print(f"    Processed: {results['stats']['events']['processed']}")
        print(f"    Failed: {results['stats']['events']['failed']}")
        print(f"    Skipped: {results['stats']['events']['skipped']}")
        print(f"\n  Conversations:")
        print(f"    Total: {results['stats']['conversations']['total']}")
        print(f"    Processed: {results['stats']['conversations']['processed']}")
        print(f"    Failed: {results['stats']['conversations']['failed']}")
        print(f"    Skipped: {results['stats']['conversations']['skipped']}")

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}", exc_info=True)
        print(f"\n❌ ERROR: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
