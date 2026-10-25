{{
    config(
        materialized = "view"
    )
}}

-- Camada Bronze/Staging: Consolida histórico de avaliações reais com tipagem segura e parsing de datas
with history_ratings as (
    select
        safe_cast(trim(userId) as int64) as user_id,
        safe_cast(trim(movieId) as int64) as movie_id,
        safe_cast(trim(rating) as float64) as rating,
        trim(tstamp) as raw_ts,
        'history' as rating_origin
    from {{ source('netflix_raw', 'user_rating_history') }}
),

additional_ratings as (
    select
        safe_cast(trim(userId) as int64) as user_id,
        safe_cast(trim(movieId) as int64) as movie_id,
        safe_cast(trim(rating) as float64) as rating,
        trim(tstamp) as raw_ts,
        'additional' as rating_origin
    from {{ source('netflix_raw', 'ratings_for_additional_users') }}
),

combined as (
    select * from history_ratings
    union all
    select * from additional_ratings
),

parsed as (
    select
        user_id,
        movie_id,
        rating,
        coalesce(
            safe.parse_timestamp('%Y-%m-%d %H:%M:%S', raw_ts),
            safe.parse_timestamp('%Y-%m-%dT%H:%M:%SZ', raw_ts),
            timestamp_seconds(safe_cast(raw_ts as int64))
        ) as rating_ts,
        rating_origin
    from combined
    where user_id is not null
      and movie_id is not null
      and rating between 0.5 and 5.0
)

select
    user_id,
    movie_id,
    rating,
    rating_ts,
    date(rating_ts) as rating_date,
    extract(year from rating_ts) as rating_year,
    extract(month from rating_ts) as rating_month,
    rating_origin
from parsed
where rating_ts is not null
qualify row_number() over (
    partition by user_id, movie_id, rating_ts
    order by rating_origin asc
) = 1

