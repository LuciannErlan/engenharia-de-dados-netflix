"""Configurações centralizadas do pipeline carregadas via variáveis de ambiente."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

EXPECTED_TABLES: dict[str, str] = {
    "movies": "movies.csv",
    "user_rating_history": "user_rating_history.csv",
    "ratings_for_additional_users": "ratings_for_additional_users.csv",
    "belief_data": "belief_data.csv",
    "movie_elicitation_set": "movie_elicitation_set.csv",
    "user_recommendation_history": "user_recommendation_history.csv",
}


@dataclass(frozen=True)
class PipelineConfig:
    """Parâmetros imutáveis de execução da ingestão e Data Warehouse."""

    gcp_project_id: str
    gcp_location: str
    bq_raw_dataset: str
    bq_analytics_dataset: str
    landing_mode: str
    gcs_bucket_name: str
    movielens_url: str
    raw_dir: Path
    landing_dir: Path
    gold_cache_dir: Path

    @classmethod
    def from_env(cls) -> PipelineConfig:
        landing_mode = os.getenv("LANDING_MODE", "bigquery_sandbox").strip().lower()
        if landing_mode not in {"bigquery_sandbox", "gcs"}:
            raise ValueError(
                f"LANDING_MODE inválido: '{landing_mode}'. Use 'bigquery_sandbox' ou 'gcs'."
            )

        return cls(
            gcp_project_id=os.getenv("GCP_PROJECT_ID", "netflix-analytics-de").strip(),
            gcp_location=os.getenv("GCP_LOCATION", "us-central1").strip(),
            bq_raw_dataset=os.getenv("BQ_RAW_DATASET", "netflix_raw").strip(),
            bq_analytics_dataset=os.getenv("BQ_ANALYTICS_DATASET", "netflix_analytics").strip(),
            landing_mode=landing_mode,
            gcs_bucket_name=os.getenv("GCS_BUCKET_NAME", "netflix-analytics-de-landing").strip(),
            movielens_url=os.getenv(
                "MOVIELENS_URL",
                "https://files.grouplens.org/datasets/movielens/ml_belief_2024_data_release_2.zip",
            ).strip(),
            raw_dir=PROJECT_ROOT / "data" / "raw",
            landing_dir=PROJECT_ROOT / "data" / "landing",
            gold_cache_dir=PROJECT_ROOT / "data" / "gold_cache",
        )

