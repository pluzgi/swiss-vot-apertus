"""
Database models for Swiss Voting Assistant
SQLAlchemy ORM models for popular initiatives (Volksinitiative) and related data
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Initiative(Base):
    """Swiss popular initiative (Volksinitiative) model - upcoming ballot initiatives only"""

    __tablename__ = "initiatives"

    # Primary identification
    id = Column(Integer, primary_key=True, autoincrement=True)
    vote_id = Column(String(50), unique=True, nullable=False, index=True)
    official_number = Column(String(50), unique=True, nullable=True)

    # Basic information
    offizieller_titel = Column(Text, nullable=True)
    schlagwort = Column(String(500), nullable=True)
    abstimmungsdatum = Column(String(50), nullable=True)
    abstimmungsnummer = Column(String(50), nullable=True)
    rechtsform = Column(String(100), nullable=True)
    politikbereich = Column(Text, nullable=True)

    # Initiative details
    urheberinnen = Column(Text, nullable=True)
    unterschriften = Column(String(100), nullable=True)
    sammeldauer = Column(String(100), nullable=True)

    # Parliamentary process
    position_bundesrat = Column(String(100), nullable=True)
    position_parlament = Column(String(100), nullable=True)
    position_nationalrat = Column(Text, nullable=True)
    position_staenderat = Column(Text, nullable=True)
    behandlungsdauer_parlament = Column(String(100), nullable=True)
    geschaeftsnummer = Column(String(50), nullable=True)

    # Party positions (stored as JSON array)
    parteiparolen = Column(JSON, nullable=True)
    weitere_parolen = Column(JSON, nullable=True)
    abweichende_sektionen = Column(JSON, nullable=True)

    # Documents and links
    abstimmungstext_pdf = Column(String(500), nullable=True)
    abstimmungsbuechlein_pdf = Column(String(500), nullable=True)
    botschaft_des_bundesrats_pdf = Column(String(500), nullable=True)
    vorpruefung_pdf = Column(String(500), nullable=True)
    zustandekommen_pdf = Column(String(500), nullable=True)

    details_url = Column(String(500), nullable=True)
    beschreibung_annee_politique_suisse_url = Column(String(500), nullable=True)
    offizielle_chronologie_url = Column(String(500), nullable=True)
    parlamentsberatung_url = Column(String(500), nullable=True)
    online_informationen_behoerden_url = Column(String(500), nullable=True)
    kampagnenfinanzierung_url = Column(String(500), nullable=True)
    waehlendenanteil_ja_lager = Column(String(500), nullable=True)

    # Brochure texts (stored as JSON with language keys: de, fr, it)
    brochure_texts = Column(JSON, nullable=True)

    # Additional metadata
    title_de = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Initiative(vote_id='{self.vote_id}', titel='{self.schlagwort}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "vote_id": self.vote_id,
            "official_number": self.official_number,
            "offizieller_titel": self.offizieller_titel,
            "schlagwort": self.schlagwort,
            "abstimmungsdatum": self.abstimmungsdatum,
            "abstimmungsnummer": self.abstimmungsnummer,
            "rechtsform": self.rechtsform,
            "politikbereich": self.politikbereich,
            "urheberinnen": self.urheberinnen,
            "unterschriften": self.unterschriften,
            "sammeldauer": self.sammeldauer,
            "position_bundesrat": self.position_bundesrat,
            "position_parlament": self.position_parlament,
            "position_nationalrat": self.position_nationalrat,
            "position_staenderat": self.position_staenderat,
            "parteiparolen": self.parteiparolen,
            "weitere_parolen": self.weitere_parolen,
            "abstimmungsbuechlein_pdf": self.abstimmungsbuechlein_pdf,
            "brochure_texts": self.brochure_texts,
            "details_url": self.details_url,
            "online_informationen_behoerden_url": self.online_informationen_behoerden_url,
        }


class BrochureChunk(Base):
    """Text chunks from official voting brochures (Abstimmungsbüchlein) for RAG"""

    __tablename__ = "brochure_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vote_id = Column(String(50), nullable=False, index=True)
    language = Column(String(10), nullable=False)  # de, fr, it
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    # ChromaDB reference
    chroma_id = Column(String(100), unique=True, nullable=True)

    # Metadata
    chunk_size = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<BrochureChunk(vote_id='{self.vote_id}', lang='{self.language}', chunk={self.chunk_index})>"


class QueryLog(Base):
    """Log of user queries for analytics"""

    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    query_language = Column(String(10), nullable=True)

    # Response metadata
    response_time_ms = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)

    # Retrieved context
    retrieved_vote_ids = Column(JSON, nullable=True)
    num_chunks_retrieved = Column(Integer, nullable=True)

    # Success/error tracking
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<QueryLog(id={self.id}, success={self.success})>"
