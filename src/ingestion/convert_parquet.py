"""Conversão otimizada de CSV bruto para Apache Parquet colunar (camada Landing / Bronze)."""

from __future__ import annotations

import csv as std_csv
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

from src.ingestion.config import PipelineConfig

logger = logging.getLogger(__name__)

_YEAR_REGEX = re.compile(r"\((\d{4})\)\s*$")


@dataclass(frozen=True)
class ParquetConversionStats:
    """Métricas de conversão de um arquivo CSV para Parquet."""

    table_name: str
    csv_path: Path
    parquet_path: Path
    row_count: int
    csv_size_mb: float
    parquet_size_mb: float
    compression_ratio_pct: float


def extract_release_year(title: str | None) -> int | None:
    """Extrai o ano de lançamento do final do título MovieLens (ex.: 'Toy Story (1995)' -> 1995)."""
    if not title:
        return None
    match = _YEAR_REGEX.search(title.strip())
    return int(match.group(1)) if match else None


def clean_movie_title(title: str | None) -> str:
    """Remove o sufixo '(YYYY)' e espaços extras preservando a caixa original do título."""
    if not title:
        return ""
    cleaned = _YEAR_REGEX.sub("", title.strip()).strip()
    return cleaned if cleaned else title.strip()


def parse_genres_pipe(genres_raw: str | None) -> list[str]:
    """Separa gêneros delimitados por '|' descartando marcadores vazios ou '(no genres listed)'."""
    if not genres_raw:
        return []
    normalized = genres_raw.strip()
    if not normalized or normalized.lower() == "(no genres listed)":
        return []
    seen: list[str] = []
    for item in normalized.split("|"):
        genre = item.strip()
        if genre and genre.lower() != "(no genres listed)" and genre not in seen:
            seen.append(genre)
    return seen


def _read_csv_header(csv_path: Path) -> list[str]:
    """Lê apenas a primeira linha do CSV para mapear todas as colunas originais como STRING."""
    with open(csv_path, encoding="utf-8", newline="") as fh:
        reader = std_csv.reader(fh)
        header = next(reader, None)
    if not header:
        raise ValueError(f"Cabeçalho vazio ou inválido no arquivo CSV: {csv_path}")
    return [col.strip() for col in header]


def convert_csv_to_parquet(
    table_name: str,
    csv_path: Path,
    landing_dir: Path,
    force: bool = False,
) -> ParquetConversionStats:
    """Converte um CSV em Parquet (ZSTD) via streaming Arrow mantendo colunas Bronze como STRING."""
    landing_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = landing_dir / f"{table_name}.parquet"
    csv_size_mb = csv_path.stat().st_size / (1024 * 1024)

    if not force and parquet_path.exists() and parquet_path.stat().st_size > 0:
        meta = pq.read_metadata(parquet_path)
        pq_size_mb = parquet_path.stat().st_size / (1024 * 1024)
        ratio = (1.0 - (pq_size_mb / csv_size_mb)) * 100 if csv_size_mb > 0 else 0.0
        logger.info(
            "Parquet já existente para %-28s | %10d linhas | %.2f MB (redução %.1f%%)",
            table_name,
            meta.num_rows,
            pq_size_mb,
            ratio,
        )
        return ParquetConversionStats(
            table_name=table_name,
            csv_path=csv_path,
            parquet_path=parquet_path,
            row_count=meta.num_rows,
            csv_size_mb=csv_size_mb,
            parquet_size_mb=pq_size_mb,
            compression_ratio_pct=ratio,
        )

    columns = _read_csv_header(csv_path)
    column_types = {col: pa.string() for col in columns}
    ingested_at_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    read_opts = pacsv.ReadOptions(block_size=16 * 1024 * 1024, encoding="utf-8")
    parse_opts = pacsv.ParseOptions(delimiter=",", quote_char='"', newlines_in_values=True)
    convert_opts = pacsv.ConvertOptions(
        column_types=column_types,
        strings_can_be_null=True,
    )

    total_rows = 0
    writer: pq.ParquetWriter | None = None
    temp_parquet = landing_dir / f".{table_name}.parquet.tmp"

    try:
        with pacsv.open_csv(
            csv_path,
            read_options=read_opts,
            parse_options=parse_opts,
            convert_options=convert_opts,
        ) as reader:
            for batch in reader:
                n = batch.num_rows
                ingested_arr = pa.array([ingested_at_iso] * n, type=pa.string())
                source_arr = pa.array([csv_path.name] * n, type=pa.string())
                enriched_batch = batch.append_column("_ingested_at", ingested_arr).append_column(
                    "_source_file", source_arr
                )

                if writer is None:
                    writer = pq.ParquetWriter(
                        temp_parquet,
                        enriched_batch.schema,
                        compression="zstd",
                    )
                writer.write_batch(enriched_batch)
                total_rows += n
    finally:
        if writer is not None:
            writer.close()

    if temp_parquet.exists():
        temp_parquet.replace(parquet_path)

    pq_size_mb = parquet_path.stat().st_size / (1024 * 1024)
    ratio = (1.0 - (pq_size_mb / csv_size_mb)) * 100 if csv_size_mb > 0 else 0.0
    logger.info(
        "Convertido %-28s | %10d linhas | CSV: %6.2f MB -> Parquet: %6.2f MB (-%.1f%%)",
        table_name,
        total_rows,
        csv_size_mb,
        pq_size_mb,
        ratio,
    )

    return ParquetConversionStats(
        table_name=table_name,
        csv_path=csv_path,
        parquet_path=parquet_path,
        row_count=total_rows,
        csv_size_mb=csv_size_mb,
        parquet_size_mb=pq_size_mb,
        compression_ratio_pct=ratio,
    )


def convert_all_to_parquet(
    csv_files: dict[str, Path],
    config: PipelineConfig,
    force: bool = False,
) -> list[ParquetConversionStats]:
    """Converte todos os CSVs extraídos para Parquet na camada Landing."""
    results: list[ParquetConversionStats] = []
    for table_name, csv_path in csv_files.items():
        stats = convert_csv_to_parquet(
            table_name=table_name,
            csv_path=csv_path,
            landing_dir=config.landing_dir,
            force=force,
        )
        results.append(stats)
    return results

