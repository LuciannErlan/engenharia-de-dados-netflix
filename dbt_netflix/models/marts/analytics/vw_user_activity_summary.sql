{{
    config(
        materialized = "view"
    )
}}

-- View para Tabela de Atividade de Usuários no Metabase e Streamlit
select
    user_id,
    activity_tier,
    total_ratings,
    unique_movies_rated,
    round(avg_rating, 2) as avg_rating,
    round(stddev_rating, 2) as stddev_rating,
    date(first_rating_ts) as first_rating_date,
    date(last_rating_ts) as last_rating_date,
    active_days_span
from {{ ref('dim_users') }}

