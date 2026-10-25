{% set partition_cfg = (
    none
    if var('is_bigquery_sandbox', true)
    else {"field": "rating_date", "data_type": "date", "granularity": "month"}
) %}

{{
    config(
        materialized = "table",
        hours_to_expiration = var('sandbox_hours_to_expiration', 1400),
        partition_by = partition_cfg,
        cluster_by = ["movie_id", "user_id"]
    )
}}

-- Tabela Fato de Avaliações Reais com integridade referencial garantida via WHERE EXISTS
select
    to_hex(md5(concat(cast(r.user_id as string), '|', cast(r.movie_id as string), '|', cast(r.rating_ts as string)))) as rating_sk,
    r.user_id,
    r.movie_id,
    cast(format_date('%Y%m%d', r.rating_date) as int64) as date_key,
    r.rating,
    r.rating_ts,
    r.rating_date,
    r.rating_year,
    r.rating_month,
    r.rating_origin
from {{ ref('stg_ratings') }} as r
where exists (
    select 1
    from {{ ref('stg_movies') }} as m
    where m.movie_id = r.movie_id
)

