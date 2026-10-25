"""Exporta as views analíticas Gold do BigQuery para Parquet local (acelerando o Streamlit e deploy Cloud)."""

from __future__ import annotations

import logging
import sys

import pyarrow.parquet as pq
from google.cloud import bigquery

from src.ingestion.config import PipelineConfig

GOLD_VIEWS_TO_EXPORT: dict[str, str] = {
    "vw_kpi_overview": "SELECT * FROM `{project}.{dataset}.vw_kpi_overview`",
    "vw_ratings_heatmap_monthly": "SELECT * FROM `{project}.{dataset}.vw_ratings_heatmap_monthly` ORDER BY rating_year, rating_month",
    "vw_top_movies_ranking": "SELECT * FROM `{project}.{dataset}.vw_top_movies_ranking` ORDER BY weighted_score DESC LIMIT 500",
    "vw_movies_popularity_vs_quality": "SELECT * FROM `{project}.{dataset}.vw_movies_popularity_vs_quality` ORDER BY total_ratings DESC LIMIT 3000",
    "vw_genre_popularity_quality": "SELECT * FROM `{project}.{dataset}.vw_genre_popularity_quality` ORDER BY total_ratings DESC",
    "vw_user_activity_summary": "SELECT * FROM `{project}.{dataset}.vw_user_activity_summary` ORDER BY total_ratings DESC LIMIT 1000",
    "vw_recsys_belief_vs_reality": "SELECT * FROM `{project}.{dataset}.vw_recsys_belief_vs_reality` ORDER BY source_id",
    "vw_recsys_certainty_calibration": "SELECT * FROM `{project}.{dataset}.vw_recsys_certainty_calibration` ORDER BY user_certainty",
}


def export_gold_views() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    config = PipelineConfig.from_env()
    config.gold_cache_dir.mkdir(parents=True, exist_ok=True)

    client = bigquery.Client(project=config.gcp_project_id, location=config.gcp_location)

    for view_name, sql_template in GOLD_VIEWS_TO_EXPORT.items():
        sql = sql_template.format(
            project=config.gcp_project_id,
            dataset=config.bq_analytics_dataset,
        )
        job_config = bigquery.QueryJobConfig(labels={"datacloud": "antigravity"})
        arrow_table = client.query(sql, job_config=job_config).to_arrow()
        out_path = config.gold_cache_dir / f"{view_name}.parquet"
        pq.write_table(arrow_table, out_path, compression="zstd")
        logging.info(
            "Cache Gold exportado: %-34s | %6d linhas -> %s",
            view_name,
            arrow_table.num_rows,
            out_path.name,
        )


if __name__ == "__main__":
    export_gold_views()
    sys.exit(0)

