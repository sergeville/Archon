"""
Backfill script to generate embeddings for existing tasks and projects.

This script:
1. Fetches all tasks and projects without embeddings
2. Generates embeddings using EmbeddingService
3. Updates database with generated embeddings
4. Provides progress tracking and error handling

Run with:
    uv run python scripts/backfill_embeddings.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from server.utils import get_supabase_client
from server.utils.embeddings import get_embedding_service
from server.config.logfire_config import get_logger

logger = get_logger(__name__)


async def backfill_task_embeddings():
    """Generate and store embeddings for all tasks."""
    supabase = get_supabase_client()
    embedding_service = get_embedding_service()

    try:
        # Fetch tasks without embeddings
        response = supabase.table("archon_tasks").select(
            "id, title, description"
        ).is_("embedding", "null").execute()

        tasks = response.data or []
        total = len(tasks)

        if total == 0:
            logger.info("No tasks need embedding backfill")
            return 0

        logger.info(f"Backfilling embeddings for {total} tasks")

        success_count = 0
        error_count = 0

        for i, task in enumerate(tasks, 1):
            try:
                # Generate embedding using EmbeddingService
                embedding = await embedding_service.generate_task_embedding(task)

                if embedding:
                    # Update task with embedding
                    supabase.table("archon_tasks").update({
                        "embedding": embedding
                    }).eq("id", task["id"]).execute()

                    success_count += 1
                    logger.info(
                        f"[{i}/{total}] Generated embedding for task: {task['title'][:50]}"
                    )
                else:
                    error_count += 1
                    logger.warning(
                        f"[{i}/{total}] Failed to generate embedding for task: {task['id']}"
                    )

                # Rate limiting - wait between requests
                if i < total:
                    await asyncio.sleep(0.5)

            except Exception as e:
                error_count += 1
                logger.error(
                    f"[{i}/{total}] Error processing task {task['id']}: {e}",
                    exc_info=True
                )

        logger.info(
            f"Task embedding backfill complete: {success_count} success, "
            f"{error_count} errors out of {total} tasks"
        )

        return success_count

    except Exception as e:
        logger.error(f"Failed to backfill task embeddings: {e}", exc_info=True)
        raise


async def backfill_project_embeddings():
    """Generate and store embeddings for all projects."""
    supabase = get_supabase_client()
    embedding_service = get_embedding_service()

    try:
        # Fetch projects without embeddings
        response = supabase.table("archon_projects").select(
            "id, title, description, features"
        ).is_("embedding", "null").execute()

        projects = response.data or []
        total = len(projects)

        if total == 0:
            logger.info("No projects need embedding backfill")
            return 0

        logger.info(f"Backfilling embeddings for {total} projects")

        success_count = 0
        error_count = 0

        for i, project in enumerate(projects, 1):
            try:
                # Generate embedding using EmbeddingService
                embedding = await embedding_service.generate_project_embedding(project)

                if embedding:
                    # Update project with embedding
                    supabase.table("archon_projects").update({
                        "embedding": embedding
                    }).eq("id", project["id"]).execute()

                    success_count += 1
                    logger.info(
                        f"[{i}/{total}] Generated embedding for project: {project['title'][:50]}"
                    )
                else:
                    error_count += 1
                    logger.warning(
                        f"[{i}/{total}] Failed to generate embedding for project: {project['id']}"
                    )

                # Rate limiting - wait between requests
                if i < total:
                    await asyncio.sleep(0.5)

            except Exception as e:
                error_count += 1
                logger.error(
                    f"[{i}/{total}] Error processing project {project['id']}: {e}",
                    exc_info=True
                )

        logger.info(
            f"Project embedding backfill complete: {success_count} success, "
            f"{error_count} errors out of {total} projects"
        )

        return success_count

    except Exception as e:
        logger.error(f"Failed to backfill project embeddings: {e}", exc_info=True)
        raise


async def main():
    """Main entry point for backfill script."""
    logger.info("=== Starting Embedding Backfill ===")

    try:
        # Backfill tasks
        task_count = await backfill_task_embeddings()

        # Backfill projects
        project_count = await backfill_project_embeddings()

        logger.info(
            f"\n=== Backfill Complete ===\n"
            f"Tasks updated: {task_count}\n"
            f"Projects updated: {project_count}\n"
            f"Total embeddings generated: {task_count + project_count}"
        )

    except Exception as e:
        logger.error("Backfill failed", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
