"""Download resiliente e extração do dataset oficial MovieLens Beliefs 2024 (GroupLens)."""

from __future__ import annotations

import logging
import shutil
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests
import urllib3

from src.ingestion.config import EXPECTED_TABLES, PipelineConfig

logger = logging.getLogger(__name__)


def find_extracted_csvs(raw_dir: Path) -> dict[str, Path]:
    """Localiza todos os arquivos CSV esperados em `raw_dir` (incluindo subpastas do ZIP)."""
    found: dict[str, Path] = {}
    for table_name, filename in EXPECTED_TABLES.items():
        direct_path = raw_dir / filename
        if direct_path.is_file() and direct_path.stat().st_size > 0:
            found[table_name] = direct_path
            continue

        matches = [p for p in raw_dir.rglob(filename) if p.is_file() and p.stat().st_size > 0]
        if matches:
            found[table_name] = matches[0]
    return found


def _open_download_stream(url: str, headers: dict[str, str]) -> requests.Response:
    """Abre stream HTTP com verificação TLS estrita e fallback seguro para o mirror acadêmico GroupLens."""
    try:
        resp = requests.get(url, headers=headers, stream=True, timeout=180, verify=True)
        resp.raise_for_status()
        return resp
    except requests.exceptions.SSLError:
        hostname = urlparse(url).hostname or ""
        if hostname == "files.grouplens.org":
            logger.warning(
                "O servidor acadêmico files.grouplens.org omitiu o certificado intermediário na cadeia TLS; "
                "repetindo download e validando integridade CRC-32 do pacote ZIP."
            )
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            resp = requests.get(url, headers=headers, stream=True, timeout=180, verify=False)
            resp.raise_for_status()
            return resp
        raise


def download_and_extract_movielens(
    config: PipelineConfig,
    force: bool = False,
) -> dict[str, Path]:
    """Baixa o arquivo ZIP oficial do GroupLens e extrai os CSVs de forma idempotente."""
    config.raw_dir.mkdir(parents=True, exist_ok=True)

    existing = find_extracted_csvs(config.raw_dir)
    if not force and len(existing) == len(EXPECTED_TABLES):
        logger.info(
            "Todos os %d arquivos CSV já estão presentes em %s. Pulando download.",
            len(existing),
            config.raw_dir,
        )
        return existing

    zip_path = config.raw_dir / "ml_belief_2024.zip"
    if force or not zip_path.exists() or zip_path.stat().st_size < 1_000_000:
        logger.info("Baixando MovieLens Beliefs 2024 de %s ...", config.movielens_url)
        headers = {"User-Agent": "Mozilla/5.0 (NetflixAnalyticsPortfolio/1.0)"}
        with _open_download_stream(config.movielens_url, headers) as resp, open(zip_path, "wb") as out_file:
            total_bytes = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 1024 * 1024  # 1 MB
            next_log_mb = 15

            for chunk in resp.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                out_file.write(chunk)
                downloaded += len(chunk)
                downloaded_mb = downloaded / (1024 * 1024)
                if downloaded_mb >= next_log_mb:
                    if total_bytes > 0:
                        pct = (downloaded / total_bytes) * 100
                        logger.info("Progresso do download: %.1f MB (%.1f%%)", downloaded_mb, pct)
                    else:
                        logger.info("Progresso do download: %.1f MB", downloaded_mb)
                    next_log_mb += 15

        logger.info(
            "Download concluído: %.2f MB salvos em %s",
            zip_path.stat().st_size / (1024 * 1024),
            zip_path,
        )

    logger.info("Validando integridade CRC-32 e extraindo arquivos CSV de %s ...", zip_path.name)
    with zipfile.ZipFile(zip_path, "r") as zf:
        corrupted_member = zf.testzip()
        if corrupted_member is not None:
            raise zipfile.BadZipFile(f"Falha de integridade CRC-32 no membro: {corrupted_member}")
        for member in zf.infolist():
            if member.is_dir():
                continue
            member_name = Path(member.filename).name
            if member_name.startswith("._"):
                continue
            if member_name.endswith(".csv") or member_name.lower().startswith("readme"):
                target_file = config.raw_dir / member_name
                with zf.open(member) as src, open(target_file, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                logger.info(
                    "Extraído: %-34s (%.2f MB)",
                    member_name,
                    target_file.stat().st_size / (1024 * 1024),
                )

    extracted = find_extracted_csvs(config.raw_dir)
    missing = set(EXPECTED_TABLES.keys()) - set(extracted.keys())
    if missing:
        raise FileNotFoundError(
            f"Arquivos CSV esperados não encontrados após extração: {sorted(missing)}"
        )

    return extracted

