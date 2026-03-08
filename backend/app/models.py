"""SQLAlchemy ORM models for the OCR clinical text analysis project."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, Float, String, Text, DateTime, JSON, ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Document(Base):
    """Cached OCR analysis results for dataset-1 documents."""
    __tablename__ = "documents"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    filename      = Column(String(255), nullable=False, unique=True)
    image_path    = Column(String(500), nullable=False)
    ground_truth  = Column(Text, nullable=False)
    ocr_text      = Column(Text, nullable=False)
    cer           = Column(Float, nullable=False)
    wer           = Column(Float, nullable=False)
    accuracy      = Column(Float, nullable=False)
    cer_sub       = Column(Integer, default=0)
    cer_del       = Column(Integer, default=0)
    cer_ins       = Column(Integer, default=0)
    cer_ref_len   = Column(Integer, default=0)
    cer_edit_dist = Column(Integer, default=0)
    wer_sub       = Column(Integer, default=0)
    wer_del       = Column(Integer, default=0)
    wer_ins       = Column(Integer, default=0)
    wer_ref_words = Column(Integer, default=0)
    wer_edit_dist = Column(Integer, default=0)
    avg_word_len  = Column(Float, default=0)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class GroundTruthNote(Base):
    """User-uploaded clinical notes for pipeline experiments."""
    __tablename__ = "ground_truth_notes"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    title         = Column(String(255), nullable=False)
    image_path    = Column(String(500), nullable=True)
    true_text     = Column(Text, nullable=False)
    ocr_text      = Column(Text, nullable=True)
    ocr_method    = Column(String(50), nullable=True)
    true_summary  = Column(Text, nullable=True, default="")
    true_topic    = Column(String(100), nullable=True, default="")
    subject_area  = Column(String(100), nullable=True)
    word_count    = Column(Integer, nullable=True)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    experiments = relationship(
        "Experiment", back_populates="note", cascade="all, delete-orphan",
    )


class Experiment(Base):
    """A single pipeline run (one note x one error rate)."""
    __tablename__ = "experiments"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    note_id          = Column(Integer, ForeignKey("ground_truth_notes.id"), nullable=False)
    error_rate       = Column(Float, nullable=False)
    error_type       = Column(String(50), default="mixed")
    status           = Column(String(20), default="pending")
    run_time_seconds = Column(Float, nullable=True)
    created_at       = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    note          = relationship("GroundTruthNote", back_populates="experiments")
    stage_results = relationship(
        "StageResult", back_populates="experiment", cascade="all, delete-orphan",
    )


class StageResult(Base):
    """Per-stage metrics for a single experiment run."""
    __tablename__ = "stage_results"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id       = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    stage_name          = Column(String(50), nullable=False)
    stage_order         = Column(Integer, nullable=False)
    output_text         = Column(Text, nullable=True)
    predicted_topic     = Column(String(100), nullable=True)
    cer                 = Column(Float, nullable=True)
    wer                 = Column(Float, nullable=True)
    error_recovery_rate = Column(Float, nullable=True)
    corrections_made    = Column(Integer, nullable=True)
    rouge_1             = Column(Float, nullable=True)
    rouge_2             = Column(Float, nullable=True)
    rouge_l             = Column(Float, nullable=True)
    topic_correct       = Column(Integer, nullable=True)
    topic_confidence    = Column(Float, nullable=True)
    all_scores          = Column(JSON, nullable=True)
    processing_time_ms  = Column(Float, nullable=True)

    experiment = relationship("Experiment", back_populates="stage_results")
