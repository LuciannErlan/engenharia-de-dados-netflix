"""Testes unitários da camada de ingestão, parsing de metadados e conversão Parquet."""

from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
import pytest

from src.ingestion.config import PipelineConfig
from src.ingestion.convert_parquet import (
    clean_movie_title,
    convert_csv_to_parquet,
    extract_release_year,
    parse_genres_pipe,
)


@pytest.mark.parametrize(
    ("raw_title", "expected_year"),
    [
        ("Toy Story (1995)", 1995),
        ("Spider-Man: Across the Spider-Verse (2023) ", 2023),
        ("City of Lost Children, The (Cité des enfants perdus, La) (1995)", 1995),
        ("Babylon 5", None),
        ("", None),
        (None, None),
    ],
)
def test_extract_release_year(raw_title: str | None, expected_year: int | None) -> None:
    assert extract_release_year(raw_title) == expected_year


@pytest.mark.parametrize(
    ("raw_title", "expected_clean"),
    [
        ("Toy Story (1995)", "Toy Story"),
        ("  Matrix, The (1999)  ", "Matrix, The"),
        ("2001: A Space Odyssey (1968)", "2001: A Space Odyssey"),
        ("Untitled Movie", "Untitled Movie"),
        (None, ""),
    ],
)
def test_clean_movie_title(raw_title: str | None, expected_clean: str) -> None:
    assert clean_movie_title(raw_title) == expected_clean


def test_parse_genres_pipe() -> None:
    assert parse_genres_pipe("Adventure|Animation|Children|Comedy|Fantasy") == [
        "Adventure",
        "Animation",
        "Children",
        "Comedy",
        "Fantasy",
    ]
    assert parse_genres_pipe("(no genres listed)") == []
    assert parse_genres_pipe("Drama|Drama|Thriller") == ["Drama", "Thriller"]
    assert parse_genres_pipe(None) == []


def test_convert_csv_to_parquet_preserves_bronze_strings(tmp_path: Path) -> None:
    csv_file = tmp_path / "movies.csv"
    csv_file.write_text(
        'movieId,title,genres\n1,"Toy Story (1995)",Adventure|Animation\n2,"Jumanji (1995)",(no genres listed)\n',
        encoding="utf-8",
    )
    landing_dir = tmp_path / "landing"

    stats = convert_csv_to_parquet(
        table_name="movies",
        csv_path=csv_file,
        landing_dir=landing_dir,
        force=True,
    )

    assert stats.row_count == 2
    assert stats.parquet_path.exists()

    table = pq.read_table(stats.parquet_path)
    assert set(table.column_names) == {
        "movieId",
        "title",
        "genres",
        "_ingested_at",
        "_source_file",
    }
    assert table.column("movieId").to_pylist() == ["1", "2"]
    assert table.column("_source_file").to_pylist() == ["movies.csv", "movies.csv"]


def test_pipeline_config_rejects_invalid_landing_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANDING_MODE", "invalid_mode")
    with pytest.raises(ValueError, match="LANDING_MODE inválido"):
        PipelineConfig.from_env()


def test_arrow_date_parquet_readable_by_pandas(tmp_path: Path) -> None:
    import datetime as dt

    import pandas as pd
    import pyarrow as pa

    arrow_tbl = pa.table(
        {
            "min_rating_date": pa.array([dt.date(1996, 3, 29)], type=pa.date32()),
            "total_ratings": pa.array([5_400_000], type=pa.int64()),
        }
    )
    out = tmp_path / "kpi.parquet"
    pq.write_table(arrow_tbl, out, compression="zstd")
    loaded = pd.read_parquet(out)
    assert len(loaded) == 1
    assert int(loaded.loc[0, "total_ratings"]) == 5_400_000


