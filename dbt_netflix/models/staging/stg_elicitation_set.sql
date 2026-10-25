{{
    config(
        materialized = "view"
    )
}}

with raw_elicitation as (
    select
        safe_cast(trim(movieId) as int64) as movie_id,
        safe_cast(trim(month_idx) as int64) as month_idx,
        safe_cast(trim(source) as int64) as source_id,
        trim(tstamp) as raw_ts
    from {{ source('netflix_raw', 'movie_elicitation_set') }}
    where safe_cast(trim(movieId) as int64) is not null
)

select
    movie_id,
    month_idx,
    source_id,
    case source_id
        when 1 then 'Popularidade'
        when 2 then 'Bem Avaliado'
        when 3 then 'Lançamento Popular'
        when 4 then 'Em Tendência'
        when 5 then 'Serendipidade'
        else 'Outros'
    end as discovery_source,
    coalesce(
        safe.parse_timestamp('%Y-%m-%d %H:%M:%S', raw_ts),
        timestamp_seconds(safe_cast(raw_ts as int64))
    ) as elicitation_ts
from raw_elicitation

