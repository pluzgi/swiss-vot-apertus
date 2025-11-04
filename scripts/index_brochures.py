#!/usr/bin/env python3
"""
Brochure Indexing Script
Index voting brochure texts into ChromaDB for RAG
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from database import get_db_session
from models import Initiative
from vector_store import get_vector_store
from embeddings import get_embedding_model, prepare_brochure_for_indexing
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def index_initiative_brochures(vector_store, embedding_model):
    """Index all brochure texts from database into ChromaDB"""

    logger.info("Fetching initiatives from database...")

    with get_db_session() as session:
        initiatives = session.query(Initiative).all()
        logger.info(f"Found {len(initiatives)} initiatives")

        if not initiatives:
            logger.warning("⚠️  No initiatives found in database")
            logger.info("Run 'python scripts/migrate_data.py' first to populate database")
            return 0

        total_chunks = 0
        indexed_count = 0

        for idx, initiative in enumerate(initiatives, 1):
            vote_id = initiative.vote_id
            brochure_texts = initiative.brochure_texts

            logger.info(f"[{idx}/{len(initiatives)}] Processing {vote_id}...")

            if not brochure_texts:
                logger.info(f"  ⏭️  No brochure texts available")
                continue

            # Prepare chunks
            chunks_data = prepare_brochure_for_indexing(
                vote_id=vote_id,
                brochure_texts=brochure_texts
            )

            if not chunks_data:
                logger.info(f"  ⏭️  No text chunks generated")
                continue

            logger.info(f"  📄 Generated {len(chunks_data)} chunks")

            # Extract data for indexing
            documents = [c["text"] for c in chunks_data]
            ids = [c["chunk_id"] for c in chunks_data]
            metadatas = [
                {
                    "vote_id": c["vote_id"],
                    "language": c["language"],
                    "chunk_index": c["chunk_index"],
                    "initiative_title": initiative.schlagwort or initiative.offizieller_titel or ""
                }
                for c in chunks_data
            ]

            # Generate embeddings
            logger.info(f"  🔢 Generating embeddings...")
            try:
                embeddings = embedding_model.encode(
                    documents,
                    batch_size=32,
                    show_progress=False
                )
            except Exception as e:
                logger.error(f"  ❌ Embedding generation failed: {e}")
                continue

            # Add to vector store
            logger.info(f"  💾 Indexing into ChromaDB...")
            try:
                vector_store.add_documents(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
                total_chunks += len(chunks_data)
                indexed_count += 1
                logger.info(f"  ✅ Indexed successfully")

            except Exception as e:
                logger.error(f"  ❌ Indexing failed: {e}")
                continue

    return indexed_count, total_chunks


def main():
    """Main indexing function"""
    print("=" * 60)
    print("Swiss Voting Assistant - Brochure Indexing")
    print("=" * 60)
    print()

    # Initialize vector store
    logger.info("Connecting to ChromaDB...")
    try:
        vector_store = get_vector_store()
        logger.info(f"Current collection size: {vector_store.count()} documents")
    except Exception as e:
        logger.error(f"❌ Failed to connect to ChromaDB: {e}")
        logger.error("Make sure ChromaDB is running (docker-compose up chromadb)")
        sys.exit(1)

    # Initialize embedding model
    logger.info("Loading embedding model...")
    try:
        embedding_model = get_embedding_model()
    except Exception as e:
        logger.error(f"❌ Failed to load embedding model: {e}")
        sys.exit(1)

    # Index brochures
    logger.info("Starting indexing process...")
    print()

    try:
        indexed_count, total_chunks = index_initiative_brochures(
            vector_store,
            embedding_model
        )
    except Exception as e:
        logger.error(f"❌ Indexing failed: {e}")
        sys.exit(1)

    # Summary
    print()
    print("=" * 60)
    print("Indexing Summary")
    print("=" * 60)
    print(f"✅ Initiatives indexed: {indexed_count}")
    print(f"📄 Total chunks created: {total_chunks}")
    print(f"💾 Collection size: {vector_store.count()} documents")
    print()

    if indexed_count > 0:
        logger.info("🎉 Indexing completed successfully!")
    else:
        logger.warning("⚠️  No initiatives were indexed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
