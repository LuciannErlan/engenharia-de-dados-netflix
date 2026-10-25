{{
    config(
        materialized = "table",
        hours_to_expiration = var('sandbox_hours_to_expiration', 1400),
        cluster_by = ["source_id", "is_seen_code"]
    )
}}

-- Tabela Fato de Crenças e Recomendações enriquecida com a estratégia de seleção (movie_elicitation_set)
with elicitation_lookup as (
    select
        movie_id,
        month_idx,
        source_id,
        discovery_source
    from {{ ref('stg_elicitation_set') }}
    qualify row_number() over (
        partition by movie_id, month_idx
        order by source_id asc
    ) = 1
),

movie_fallback_source as (
    select
        movie_id,
        source_id,
        discovery_source
    from {{ ref('stg_elicitation_set') }}
    qualify row_number() over (
        partition by movie_id
        order by month_idx desc, source_id asc
    ) = 1
)

select
    to_hex(md5(concat(
        cast(b.user_id as string), '|',
        cast(b.movie_id as string), '|',
        coalesce(cast(b.belief_ts as string), ''), '|',
        coalesce(cast(b.month_idx as string), '')
    ))) as belief_sk,
    b.user_id,
    b.movie_id,
    b.is_seen_code,
    b.seen_status,
    b.watch_date,
    b.user_predict_rating,
    b.user_elicit_rating,
    b.system_predict_rating,
    b.user_certainty,
    -- Quando o usuário já assistiu (isSeen=1): diferença entre nota real e nota prevista pelo sistema
    round(b.user_elicit_rating - b.system_predict_rating, 4) as expectation_surprise_gap,
    -- Erro absoluto do algoritmo frente à nota real pós-assistir
    round(abs(b.user_elicit_rating - b.system_predict_rating), 4) as system_abs_error,
    -- Divergência absoluta entre expectativa humana prévia (isSeen=0) e previsão do algoritmo
    round(abs(b.user_predict_rating - b.system_predict_rating), 4) as user_abs_error,
    b.month_idx,
    b.elicitation_bucket_id,
    b.elicitation_bucket,
    coalesce(el.source_id, mf.source_id, 0) as source_id,
    coalesce(el.discovery_source, mf.discovery_source, 'Catálogo Geral') as discovery_source,
    b.belief_ts
from {{ ref('stg_beliefs') }} as b
left join elicitation_lookup as el
    on b.movie_id = el.movie_id
   and b.month_idx = el.month_idx
left join movie_fallback_source as mf
    on b.movie_id = mf.movie_id
where exists (
    select 1
    from {{ ref('stg_movies') }} as m
    where m.movie_id = b.movie_id
)
