#!/usr/bin/env python3
"""
Data Migration Script
Migrate voting data from JSON to PostgreSQL database
"""

import json
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from database import init_db, get_db_session, test_connection
from models import Initiative
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def load_json_data(json_path: str) -> dict:
    """Load voting data from JSON file"""
    logger.info(f"Loading data from {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data.get('federal_votes', []))} initiatives")
    return data


def migrate_initiative(session, vote_data: dict) -> Initiative:
    """Migrate single initiative to database"""

    # Check if already exists
    existing = session.query(Initiative).filter(
        Initiative.vote_id == vote_data.get('vote_id')
    ).first()

    if existing:
        logger.info(f"  Updating existing initiative {vote_data.get('vote_id')}")
        initiative = existing
    else:
        logger.info(f"  Creating new initiative {vote_data.get('vote_id')}")
        initiative = Initiative()

    # Map JSON fields to model fields
    initiative.vote_id = vote_data.get('vote_id')
    initiative.official_number = vote_data.get('official_number')
    initiative.offizieller_titel = vote_data.get('offizieller_titel')
    initiative.schlagwort = vote_data.get('schlagwort')
    initiative.abstimmungsdatum = vote_data.get('abstimmungsdatum')
    initiative.abstimmungsnummer = vote_data.get('abstimmungsnummer')
    initiative.rechtsform = vote_data.get('rechtsform')
    initiative.politikbereich = vote_data.get('politikbereich')

    # Initiative details
    initiative.urheberinnen = vote_data.get('urheberinnen')
    initiative.unterschriften = vote_data.get('unterschriften')
    initiative.sammeldauer = vote_data.get('sammeldauer')

    # Parliamentary process
    initiative.position_bundesrat = vote_data.get('position_bundesrat')
    initiative.position_parlament = vote_data.get('position_parlament')
    initiative.position_nationalrat = vote_data.get('position_nationalrat')
    initiative.position_staenderat = vote_data.get('position_staenderat')
    initiative.behandlungsdauer_parlament = vote_data.get('behandlungsdauer_parlament')
    initiative.geschaeftsnummer = vote_data.get('geschaeftsnummer')

    # Party positions (JSON)
    initiative.parteiparolen = vote_data.get('parteiparolen', [])
    initiative.weitere_parolen = vote_data.get('weitere_parolen', [])
    initiative.abweichende_sektionen = vote_data.get('abweichende_sektionen', [])

    # Documents
    initiative.abstimmungstext_pdf = vote_data.get('abstimmungstext_pdf')
    initiative.abstimmungsbuechlein_pdf = vote_data.get('abstimmungsbuechlein_pdf')
    initiative.botschaft_des_bundesrats_pdf = vote_data.get('botschaft_des_bundesrats_pdf')
    initiative.vorpruefung_pdf = vote_data.get('vorpruefung_pdf')
    initiative.zustandekommen_pdf = vote_data.get('zustandekommen_pdf')

    # Links
    initiative.details_url = vote_data.get('details_url')
    initiative.beschreibung_annee_politique_suisse_url = vote_data.get('beschreibung_annee_politique_suisse_url')
    initiative.offizielle_chronologie_url = vote_data.get('offizielle_chronologie_url')
    initiative.parlamentsberatung_url = vote_data.get('parlamentsberatung_url')
    initiative.online_informationen_behoerden_url = vote_data.get('online_informationen_behoerden_url')
    initiative.kampagnenfinanzierung_url = vote_data.get('kampagnenfinanzierung_url')
    initiative.waehlendenanteil_ja_lager = vote_data.get('waehlendenanteil_ja_lager')

    # Brochure texts (JSON)
    initiative.brochure_texts = vote_data.get('brochure_texts', {})

    # Additional
    initiative.title_de = vote_data.get('title_de')

    if not existing:
        session.add(initiative)

    return initiative


def main():
    """Main migration function"""
    print("=" * 60)
    print("Swiss Voting Assistant - Data Migration")
    print("=" * 60)
    print()

    # Find JSON file
    json_path = Path(__file__).parent.parent / "servers" / "swiss-voting" / "data" / "current_votes.json"

    if not json_path.exists():
        logger.error(f"❌ JSON file not found: {json_path}")
        sys.exit(1)

    # Test database connection
    logger.info("Testing database connection...")
    if not test_connection():
        logger.error("❌ Database connection failed. Check your DATABASE_URL in .env")
        sys.exit(1)

    # Initialize database (create tables if they don't exist)
    logger.info("Initializing database tables...")
    try:
        init_db()
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        sys.exit(1)

    # Load JSON data
    try:
        data = load_json_data(json_path)
    except Exception as e:
        logger.error(f"❌ Failed to load JSON data: {e}")
        sys.exit(1)

    # Migrate data
    logger.info("Starting migration...")
    initiatives = data.get('federal_votes', [])

    if not initiatives:
        logger.warning("⚠️  No initiatives found in JSON file")
        sys.exit(0)

    with get_db_session() as session:
        success_count = 0
        error_count = 0

        for idx, vote_data in enumerate(initiatives, 1):
            try:
                logger.info(f"[{idx}/{len(initiatives)}] Processing initiative {vote_data.get('vote_id')}...")
                migrate_initiative(session, vote_data)
                success_count += 1
            except Exception as e:
                logger.error(f"  ❌ Error: {e}")
                error_count += 1

        # Commit happens automatically in context manager

    # Summary
    print()
    print("=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Total: {len(initiatives)}")
    print()

    if error_count == 0:
        logger.info("🎉 Migration completed successfully!")
    else:
        logger.warning(f"⚠️  Migration completed with {error_count} errors")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
