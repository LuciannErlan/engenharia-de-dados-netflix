"""Provisionamento BI-as-Code do Metabase conectado ao Google BigQuery.

Automatiza via API REST oficial do Metabase (v0.50+ / MBQL 5):
1. Setup inicial (ou login idempotente) do administrador local;
2. Conexão segura ao Google BigQuery (`bigquery-cloud-sdk`) via Service Account least-privilege;
3. Criação de Collection dedicada e 9 Questions (Cards) analíticas sobre a camada Gold (`netflix_analytics`);
4. Construção do Dashboard executivo em grade responsiva (24 colunas) e ativação de link público compartilhável.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class CardSpec:
    name: str
    description: str
    display: str
    sql: str
    visualization_settings: dict[str, Any]
    row: int
    col: int
    size_x: int
    size_y: int


def build_card_specs(project_id: str, dataset_id: str) -> list[CardSpec]:
    fqn = f"`{project_id}.{dataset_id}"
    return [
        CardSpec(
            name="1. KPIs Globais da Plataforma (Catálogo, Audiência e RecSys)",
            description="Resumo executivo consolidado da camada Gold no BigQuery.",
            display="table",
            sql=f"""
SELECT
    total_catalog_movies AS catalogo_total_filmes,
    rated_movies_count AS filmes_avaliados,
    total_ratings AS total_avaliacoes_unicas,
    total_active_users AS usuarios_ativos,
    global_avg_rating AS nota_media_global,
    global_stddev_rating AS desvio_padrao_global,
    total_belief_records AS interacoes_beliefs,
    global_system_mae AS mae_algoritmo_recomendacao
FROM {fqn}.vw_kpi_overview`
""".strip(),
            visualization_settings={},
            row=0,
            col=0,
            size_x=24,
            size_y=4,
        ),
        CardSpec(
            name="2. Evolução de Ratings ao Longo do Tempo (Série Mensal)",
            description="Sazonalidade e volume mensal de avaliações na plataforma desde 2010.",
            display="area",
            sql=f"""
SELECT
    year_month AS ano_mes,
    total_ratings AS total_avaliacoes,
    avg_rating AS nota_media
FROM {fqn}.vw_ratings_heatmap_monthly`
WHERE rating_year >= 2010
ORDER BY rating_year, rating_month
""".strip(),
            visualization_settings={
                "graph.dimensions": ["ano_mes"],
                "graph.metrics": ["total_avaliacoes"],
            },
            row=4,
            col=0,
            size_x=24,
            size_y=7,
        ),
        CardSpec(
            name="3. Top 10 Filmes — Melhor Qualidade (Score Bayesiano)",
            description="Ranking ponderado pela confiança estatística de votos (mínimo 100 avaliações).",
            display="row",
            sql=f"""
SELECT
    clean_title AS filme,
    weighted_score AS score_bayesiano,
    avg_rating AS nota_media,
    total_ratings AS total_avaliacoes
FROM {fqn}.vw_top_movies_ranking`
WHERE total_ratings >= 100
ORDER BY weighted_score DESC
LIMIT 10
""".strip(),
            visualization_settings={
                "graph.dimensions": ["filme"],
                "graph.metrics": ["score_bayesiano"],
            },
            row=11,
            col=0,
            size_x=12,
            size_y=8,
        ),
        CardSpec(
            name="4. Top 10 Filmes — Mais Avaliados (Popularidade)",
            description="Títulos líderes em alcance histórico e volume absoluto de avaliações.",
            display="row",
            sql=f"""
SELECT
    clean_title AS filme,
    total_ratings AS total_avaliacoes,
    avg_rating AS nota_media
FROM {fqn}.vw_movies_popularity_vs_quality`
ORDER BY total_ratings DESC
LIMIT 10
""".strip(),
            visualization_settings={
                "graph.dimensions": ["filme"],
                "graph.metrics": ["total_avaliacoes"],
            },
            row=11,
            col=12,
            size_x=12,
            size_y=8,
        ),
        CardSpec(
            name="5. Popularidade dos Gêneros Cinematográficos",
            description="Volume de avaliações por gênero (explosão N:N via bridge_movie_genres).",
            display="row",
            sql=f"""
SELECT
    genre_name AS genero,
    total_ratings AS total_avaliacoes,
    total_movies AS qtd_filmes,
    avg_rating AS nota_media
FROM {fqn}.vw_genre_popularity_quality`
ORDER BY total_ratings DESC
""".strip(),
            visualization_settings={
                "graph.dimensions": ["genero"],
                "graph.metrics": ["total_avaliacoes"],
            },
            row=19,
            col=0,
            size_x=12,
            size_y=8,
        ),
        CardSpec(
            name="6. Gênero: Popularidade vs. Qualidade (Scatter Plot)",
            description="Relação entre volume de votos, nota média e tamanho do catálogo por gênero.",
            display="scatter",
            sql=f"""
SELECT
    genre_name AS genero,
    total_ratings AS popularidade_votos,
    avg_rating AS qualidade_media,
    total_movies AS tamanho_catalogo
FROM {fqn}.vw_genre_popularity_quality`
""".strip(),
            visualization_settings={
                "graph.dimensions": ["popularidade_votos", "genero"],
                "graph.metrics": ["qualidade_media"],
                "scatter.bubble": "tamanho_catalogo",
            },
            row=19,
            col=12,
            size_x=12,
            size_y=8,
        ),
        CardSpec(
            name="7. Filmes: Popularidade vs. Qualidade (Quadrantes Analíticos)",
            description="Dispersão dos 1.000 filmes mais avaliados entre alcance e nota média.",
            display="scatter",
            sql=f"""
SELECT
    clean_title AS filme,
    total_ratings AS popularidade_votos,
    avg_rating AS qualidade_media,
    stddev_rating AS desvio_padrao,
    quadrant_label AS quadrante
FROM {fqn}.vw_movies_popularity_vs_quality`
WHERE total_ratings >= 100
ORDER BY total_ratings DESC
LIMIT 1000
""".strip(),
            visualization_settings={
                "graph.dimensions": ["popularidade_votos", "quadrante"],
                "graph.metrics": ["qualidade_media"],
            },
            row=27,
            col=0,
            size_x=12,
            size_y=8,
        ),
        CardSpec(
            name="8. Lab de Recomendação — Expectativa Humana vs. Algoritmo vs. Nota Real",
            description="Comparação das notas antes e depois de assistir por canal de descoberta (belief_data).",
            display="bar",
            sql=f"""
SELECT
    discovery_source AS canal_recomendacao,
    avg_user_predicted_rating AS expectativa_humana,
    avg_system_predicted_rating AS previsao_algoritmo,
    avg_actual_watched_rating AS nota_real_pos_assistir
FROM {fqn}.vw_recsys_belief_vs_reality`
ORDER BY source_id
""".strip(),
            visualization_settings={
                "graph.dimensions": ["canal_recomendacao"],
                "graph.metrics": [
                    "expectativa_humana",
                    "previsao_algoritmo",
                    "nota_real_pos_assistir",
                ],
            },
            row=27,
            col=12,
            size_x=12,
            size_y=8,
        ),
        CardSpec(
            name="9. Atividade Comportamental de Usuários (Top 100)",
            description="Segmentação de usuários por volume, rigor crítico (σ) e janela de retenção.",
            display="table",
            sql=f"""
SELECT
    user_id,
    activity_tier AS segmento,
    total_ratings AS avaliacoes,
    avg_rating AS nota_media,
    stddev_rating AS desvio_padrao,
    first_rating_date AS primeira_avaliacao,
    last_rating_date AS ultima_avaliacao,
    active_days_span AS dias_retencao
FROM {fqn}.vw_user_activity_summary`
ORDER BY total_ratings DESC
LIMIT 100
""".strip(),
            visualization_settings={},
            row=35,
            col=0,
            size_x=24,
            size_y=8,
        ),
    ]


class MetabaseAutomator:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def authenticate_or_setup(self, email: str, password: str) -> None:
        props_resp = self.session.get(self._url("/api/session/properties"), timeout=30)
        props_resp.raise_for_status()
        props = props_resp.json()

        if not props.get("has-user-setup"):
            setup_token = props.get("setup-token")
            if not setup_token:
                raise RuntimeError("Metabase sem setup concluído, mas 'setup-token' ausente.")
            logging.info("Executando setup inicial automatizado do Metabase (%s)...", email)
            payload = {
                "token": setup_token,
                "user": {
                    "first_name": "Luciana",
                    "last_name": "Erlan",
                    "email": email,
                    "password": password,
                },
                "prefs": {
                    "site_name": "Netflix & MovieLens Analytics",
                    "site_locale": "pt_BR",
                },
            }
            resp = self.session.post(self._url("/api/setup"), json=payload, timeout=60)
            resp.raise_for_status()
            token_id = resp.json()["id"]
        else:
            logging.info("Realizando login na API do Metabase (%s)...", email)
            resp = self.session.post(
                self._url("/api/session"),
                json={"username": email, "password": password},
                timeout=30,
            )
            resp.raise_for_status()
            token_id = resp.json()["id"]

        self.session.headers.update({"X-Metabase-Session": token_id})

    def ensure_bigquery_database(
        self,
        db_name: str,
        project_id: str,
        dataset_id: str,
        sa_json_path: Path,
    ) -> int:
        if not sa_json_path.exists():
            raise FileNotFoundError(
                f"Arquivo de Service Account não encontrado em {sa_json_path}. "
                "Execute scripts/setup_gcp_service_account.ps1 primeiro."
            )
        sa_json_str = sa_json_path.read_text(encoding="utf-8")

        dbs_resp = self.session.get(self._url("/api/database"), timeout=30)
        dbs_resp.raise_for_status()
        dbs_data = dbs_resp.json()
        dbs_list = dbs_data.get("data", dbs_data) if isinstance(dbs_data, dict) else dbs_data

        for db in dbs_list:
            if db.get("name") == db_name or db.get("engine") == "bigquery-cloud-sdk":
                db_id = int(db["id"])
                logging.info("Conexão BigQuery já cadastrada no Metabase (id=%d). Sincronizando schema...", db_id)
                self.session.post(self._url(f"/api/database/{db_id}/sync_schema"), timeout=30)
                return db_id

        logging.info("Conectando Google BigQuery (%s.%s) ao Metabase...", project_id, dataset_id)
        payload = {
            "name": db_name,
            "engine": "bigquery-cloud-sdk",
            "details": {
                "project-id": project_id,
                "service-account-json": sa_json_str,
                "dataset-filters-type": "inclusion",
                "dataset-filters-patterns": dataset_id,
            },
            "is_full_sync": True,
            "auto_run_queries": True,
        }
        create_resp = self.session.post(self._url("/api/database"), json=payload, timeout=90)
        if not create_resp.ok:
            raise RuntimeError(
                f"Erro ao conectar BigQuery no Metabase ({create_resp.status_code}): {create_resp.text}"
            )
        db_id = int(create_resp.json()["id"])
        self.session.post(self._url(f"/api/database/{db_id}/sync_schema"), timeout=30)
        logging.info("Google BigQuery conectado com sucesso (database_id=%d)!", db_id)
        return db_id

    def ensure_collection(self, name: str) -> int:
        resp = self.session.get(self._url("/api/collection"), timeout=30)
        resp.raise_for_status()
        for col in resp.json():
            if col.get("name") == name and not col.get("archived"):
                return int(col["id"])

        create_resp = self.session.post(
            self._url("/api/collection"),
            json={
                "name": name,
                "description": " Análises executivas do catálogo MovieLens Beliefs 2024 no Google BigQuery.",
            },
            timeout=30,
        )
        create_resp.raise_for_status()
        return int(create_resp.json()["id"])

    def upsert_cards(self, db_id: int, collection_id: int, specs: list[CardSpec]) -> list[tuple[int, CardSpec]]:
        items_resp = self.session.get(
            self._url(f"/api/collection/{collection_id}/items"),
            params={"models": "card"},
            timeout=30,
        )
        items_resp.raise_for_status()
        existing_cards = {
            item["name"]: int(item["id"])
            for item in items_resp.json().get("data", [])
            if item.get("model") == "card"
        }

        created: list[tuple[int, CardSpec]] = []
        for spec in specs:
            card_payload = {
                "name": spec.name,
                "description": spec.description,
                "display": spec.display,
                "collection_id": collection_id,
                "dataset_query": {
                    "lib/type": "mbql/query",
                    "database": db_id,
                    "stages": [
                        {
                            "lib/type": "mbql.stage/native",
                            "native": spec.sql,
                        }
                    ],
                },
                "visualization_settings": spec.visualization_settings,
            }
            if spec.name in existing_cards:
                card_id = existing_cards[spec.name]
                r = self.session.put(self._url(f"/api/card/{card_id}"), json=card_payload, timeout=60)
                r.raise_for_status()
            else:
                r = self.session.post(self._url("/api/card"), json=card_payload, timeout=60)
                if not r.ok:
                    raise RuntimeError(f"Falha ao criar card '{spec.name}' ({r.status_code}): {r.text}")
                card_id = int(r.json()["id"])
            logging.info("Card pronto [id=%d]: %s", card_id, spec.name)
            created.append((card_id, spec))
        return created

    def upsert_dashboard_and_public_link(
        self,
        collection_id: int,
        title: str,
        cards_with_specs: list[tuple[int, CardSpec]],
    ) -> tuple[int, str]:
        items_resp = self.session.get(
            self._url(f"/api/collection/{collection_id}/items"),
            params={"models": "dashboard"},
            timeout=30,
        )
        items_resp.raise_for_status()
        existing_dash = {
            item["name"]: int(item["id"])
            for item in items_resp.json().get("data", [])
            if item.get("model") == "dashboard"
        }

        if title in existing_dash:
            dash_id = existing_dash[title]
        else:
            d_resp = self.session.post(
                self._url("/api/dashboard"),
                json={
                    "name": title,
                    "description": "Dashboard Executivo End-to-End (Parquet + Google BigQuery + dbt Core + Metabase).",
                    "collection_id": collection_id,
                },
                timeout=30,
            )
            d_resp.raise_for_status()
            dash_id = int(d_resp.json()["id"])

        dashcards = []
        for idx, (card_id, spec) in enumerate(cards_with_specs, start=1):
            dashcards.append(
                {
                    "id": -idx,
                    "card_id": card_id,
                    "row": spec.row,
                    "col": spec.col,
                    "size_x": spec.size_x,
                    "size_y": spec.size_y,
                    "parameter_mappings": [],
                    "visualization_settings": {},
                }
            )

        put_resp = self.session.put(
            self._url(f"/api/dashboard/{dash_id}"),
            json={
                "name": title,
                "width": "full",
                "dashcards": dashcards,
            },
            timeout=60,
        )
        if not put_resp.ok:
            raise RuntimeError(f"Erro ao posicionar cards no dashboard ({put_resp.status_code}): {put_resp.text}")

        # Habilita compartilhamento público na instância e gera link público do dashboard
        self.session.put(
            self._url("/api/setting/enable-public-sharing"),
            json={"value": True},
            timeout=30,
        ).raise_for_status()

        pub_resp = self.session.post(
            self._url(f"/api/dashboard/{dash_id}/public_link"),
            timeout=30,
        )
        pub_resp.raise_for_status()
        uuid = pub_resp.json()["uuid"]
        public_url = f"{self.base_url}/public/dashboard/{uuid}"
        return dash_id, public_url

    def verify_card_execution(self, card_id: int) -> int:
        resp = self.session.post(self._url(f"/api/card/{card_id}/query"), timeout=90)
        resp.raise_for_status()
        data = resp.json()
        rows = data.get("data", {}).get("rows", [])
        return len(rows)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    load_dotenv(PROJECT_ROOT / ".env")

    base_url = os.getenv("METABASE_URL", "http://localhost:3000").strip()
    admin_email = os.getenv("METABASE_ADMIN_EMAIL", "").strip()
    admin_password = os.getenv("METABASE_ADMIN_PASSWORD", "").strip()
    project_id = os.getenv("GCP_PROJECT_ID", "netflix-analytics-de").strip()
    dataset_id = os.getenv("BQ_ANALYTICS_DATASET", "netflix_analytics").strip()

    if not admin_email or not admin_password:
        raise ValueError("Defina METABASE_ADMIN_EMAIL e METABASE_ADMIN_PASSWORD no arquivo .env.")

    sa_path = PROJECT_ROOT / "secrets" / "metabase-service-account.json"

    automator = MetabaseAutomator(base_url)
    automator.authenticate_or_setup(admin_email, admin_password)
    db_id = automator.ensure_bigquery_database(
        db_name="Google BigQuery — Netflix Analytics",
        project_id=project_id,
        dataset_id=dataset_id,
        sa_json_path=sa_path,
    )
    col_id = automator.ensure_collection("Netflix & MovieLens 2024")
    specs = build_card_specs(project_id, dataset_id)
    cards = automator.upsert_cards(db_id, col_id, specs)
    dash_id, public_url = automator.upsert_dashboard_and_public_link(
        collection_id=col_id,
        title="Streaming & Recommendation Analytics — MovieLens 2024",
        cards_with_specs=cards,
    )

    first_card_id = cards[0][0]
    row_count = automator.verify_card_execution(first_card_id)
    logging.info("Teste ao vivo Metabase -> BigQuery retornou %d linha(s) com sucesso!", row_count)
    logging.info("Dashboard Interno : %s/dashboard/%d", base_url, dash_id)
    logging.info("Dashboard Público : %s", public_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())

