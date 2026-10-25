"""Carga idempotente dos arquivos Parquet na camada Raw do BigQuery (com suporte a GCS e Sandbox)."""

from __future__ import annotations

import logging
from pathlib import Path

from google.api_core.exceptions import NotFound
from google.cloud import bigquery, storage

from src.ingestion.config import PipelineConfig
from src.ingestion.convert_parquet import ParquetConversionStats

logger = logging.getLogger(__name__)

# No BigQuery Sandbox (sem faturamento), a expiração máxima permitida é 60 dias.
SANDBOX_SAFE_EXPIRATION_MS = 59 * 24 * 60 * 60 * 1000


def ensure_bigquery_dataset(
    bq_client: bigquery.Client,
    project_id: str,
    dataset_name: str,
    location: str,
    description: str,
) -> bigquery.Dataset:
    """Garante que o dataset exista no BigQuery na região configurada."""
    dataset_id = f"{project_id}.{dataset_name}"
    try:
        dataset = bq_client.get_dataset(dataset_id)
        logger.info("Dataset BigQuery já existente: %s (location=%s)", dataset_id, dataset.location)
        return dataset
    except NotFound:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = location
        dataset.description = description
        dataset.default_table_expiration_ms = SANDBOX_SAFE_EXPIRATION_MS
        dataset.labels = {"datacloud": "antigravity", "project": "netflix-portfolio"}
        created = bq_client.create_dataset(dataset, exists_ok=True)
        logger.info("Dataset BigQuery criado com sucesso: %s (%s)", dataset_id, location)
        return created


def upload_parquet_to_gcs(
    parquet_path: Path,
    bucket_name: str,
    project_id: str,
    table_name: str,
) -> str:
    """Envia arquivo Parquet para a Landing Zone no Google Cloud Storage (modo `gcs`)."""
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blob_path = f"movielens_beliefs_2024/raw/{table_name}/{parquet_path.name}"
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(str(parquet_path), timeout=300)
    gcs_uri = f"gs://{bucket_name}/{blob_path}"
    logger.info("Arquivo enviado ao GCS: %s", gcs_uri)
    return gcs_uri


def load_parquets_to_bigquery(
    parquet_stats: list[ParquetConversionStats],
    config: PipelineConfig,
) -> dict[str, int]:
    """Carrega todos os arquivos Parquet na camada `netflix_raw` do BigQuery."""
    bq_client = bigquery.Client(project=config.gcp_project_id, location=config.gcp_location)

    ensure_bigquery_dataset(
        bq_client=bq_client,
        project_id=config.gcp_project_id,
        dataset_name=config.bq_raw_dataset,
        location=config.gcp_location,
        description="Camada Raw / Bronze — MovieLens Beliefs 2024 (colunas originais em STRING + metadados).",
    )
    ensure_bigquery_dataset(
        bq_client=bq_client,
        project_id=config.gcp_project_id,
        dataset_name=config.bq_analytics_dataset,
        location=config.gcp_location,
        description="Camada Analytics (Staging / Intermediate / Gold Star Schema) gerenciada via dbt Core.",
    )

    loaded_counts: dict[str, int] = {}

    for item in parquet_stats:
        table_id = f"{config.gcp_project_id}.{config.bq_raw_dataset}.{item.table_name}"
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            labels={"datacloud": "antigravity", "layer": "bronze"},
        )

        if config.landing_mode == "gcs":
            gcs_uri = upload_parquet_to_gcs(
                parquet_path=item.parquet_path,
                bucket_name=config.gcs_bucket_name,
                project_id=config.gcp_project_id,
                table_name=item.table_name,
            )
            logger.info("Carregando %s no BigQuery a partir de %s ...", table_id, gcs_uri)
            load_job = bq_client.load_table_from_uri(
                gcs_uri,
                table_id,
                job_config=job_config,
                location=config.gcp_location,
            )
        else:
            logger.info(
                "Carregando %s no BigQuery Sandbox a partir do Data Lake local (%s) ...",
                table_id,
                item.parquet_path.name,
            )
            with open(item.parquet_path, "rb") as parquet_fp:
                load_job = bq_client.load_table_from_file(
                    parquet_fp,
                    table_id,
                    job_config=job_config,
                    location=config.gcp_location,
                )

        load_job.result()
        dest_table = bq_client.get_table(table_id)
        row_count = dest_table.num_rows or 0
        loaded_counts[item.table_name] = row_count
        logger.info("Tabela carregada com sucesso: %-45s | %10d linhas", table_id, row_count)

    return loaded_counts

