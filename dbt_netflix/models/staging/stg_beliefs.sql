{{
    config(
        materialized = "view"
    )
}}

-- Camada Bronze/Staging: Limpeza e enriquecimento semântico da tabela de crenças/expectativas (belief_data)
with raw_beliefs as (
    select
        safe_cast(trim(userId) as int64) as user_id,
        safe_cast(trim(movieId) as int64) as movie_id,
        safe_cast(trim(isSeen) as int64) as is_seen_code,
        nullif(trim(watchDate), '') as raw_watch_date,
        safe_cast(nullif(trim(userElicitRating), '-1') as float64) as raw_elicit_rating,
        safe_cast(nullif(trim(userPredictRating), '-1') as float64) as raw_predict_rating,
        safe_cast(nullif(trim(userCertainty), '-1') as int64) as raw_certainty,
        trim(tstamp) as raw_ts,
        safe_cast(trim(movie_idx) as int64) as month_idx,
        safe_cast(trim(source) as int64) as elicitation_bucket_id,
        safe_cast(nullif(trim(systemPredictRating), '-1') as float64) as raw_system_rating
    from {{ source('netflix_raw', 'belief_data') }}
    where safe_cast(trim(userId) as int64) is not null
      and safe_cast(trim(movieId) as int64) is not null
)

select
    user_id,
    movie_id,
    is_seen_code,
    case is_seen_code
        when 1 then 'Já Assistiu'
        when 0 then 'Não Assistiu'
        when -1 then 'Não Respondeu'
        else 'Desconhecido'
    end as seen_status,
    coalesce(
        safe.parse_date('%Y-%m-%d', substr(raw_watch_date, 1, 10)),
        date(safe.parse_timestamp('%Y-%m-%d %H:%M:%S', raw_watch_date))
    ) as watch_date,
    case when raw_elicit_rating between 0.5 and 5.0 then raw_elicit_rating end as user_elicit_rating,
    case when raw_predict_rating between 0.5 and 5.0 then raw_predict_rating end as user_predict_rating,
    case when raw_certainty between 1 and 5 then raw_certainty end as user_certainty,
    case when raw_system_rating between 0.5 and 5.0 then raw_system_rating end as system_predict_rating,
    coalesce(
        safe.parse_timestamp('%Y-%m-%d %H:%M:%S', raw_ts),
        timestamp_seconds(safe_cast(raw_ts as int64))
    ) as belief_ts,
    month_idx,
    elicitation_bucket_id,
    case elicitation_bucket_id
        when 1 then 'Amostragem Ampla'
        when 2 then 'Recomendação Potencial'
        when 3 then 'Novos Filmes'
        else 'Outros'
    end as elicitation_bucket
from raw_beliefs

