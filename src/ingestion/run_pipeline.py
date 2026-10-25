"""Orquestrador CLI de Ingestão: Download GroupLens -> Conversão Parquet -> Carga BigQuery."""

from __future__ import annotations

import argparse
import logging
import sys

from src.ingestion.config import PipelineConfig
from src.ingestion.convert_parquet import convert_all_to_parquet
from src.ingestion.download_dataset import download_and_extract_movielens
from src.ingestion.load_bigquery import load_parquets_to_bigquery


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingestão end-to-end MovieLens Beliefs 2024 para Parquet e Google BigQuery."
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Força novo download e extração do ZIP oficial mesmo se os CSVs já existirem.",
    )
    parser.add_argument(
        "--force-convert",
        action="store_true",
        help="Reprocessa a conversão CSV -> Parquet mesmo se os arquivos Parquet já existirem.",
    )
    parser.add_argument(
        "--only-download",
        action="store_true",
        help="Executa apenas o download e extração dos CSVs oficiais do GroupLens.",
    )
    parser.add_argument(
        "--skip-bigquery",
        action="store_true",
        help="Executa apenas download e conversão Parquet local, sem enviar ao BigQuery.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    args = parse_args(argv)
    config = PipelineConfig.from_env()

    logging.info(
        "Iniciando pipeline de ingestão | Projeto=%s | Região=%s | Modo=%s",
        config.gcp_project_id,
        config.gcp_location,
        config.landing_mode,
    )

    csv_files = download_and_extract_movielens(config=config, force=args.force_download)
    if args.only_download:
        logging.info("Download e extração finalizados (%d arquivos CSV prontos).", len(csv_files))
        return 0
    parquet_stats = convert_all_to_parquet(
        csv_files=csv_files,
        config=config,
        force=args.force_convert,
    )

    total_csv_mb = sum(s.csv_size_mb for s in parquet_stats)
    total_pq_mb = sum(s.parquet_size_mb for s in parquet_stats)
    overall_reduction = (1.0 - (total_pq_mb / total_csv_mb)) * 100 if total_csv_mb > 0 else 0.0
    logging.info(
        "Resumo Landing Zone Parquet: %.2f MB (CSV) -> %.2f MB (Parquet ZSTD) | Economia: %.1f%%",
        total_csv_mb,
        total_pq_mb,
        overall_reduction,
    )

    if not args.skip_bigquery:
        loaded = load_parquets_to_bigquery(parquet_stats=parquet_stats, config=config)
        logging.info("Carga BigQuery finalizada com sucesso para %d tabelas: %s", len(loaded), loaded)

    return 0


if __name__ == "__main__":
    sys.exit(main())

