{{
    config(
        materialized = "view"
    )
}}

with raw_recs as (
    select
        safe_cast(trim(userId) as int64) as user_id,
        safe_cast(trim(movieId) as int64) as movie_id,
        safe_cast(trim(predictedRating) as float64) as predicted_rating,
        trim(tstamp) as raw_ts
    from {{ source('netflix_raw', 'user_recommendation_history') }}
    where safe_cast(trim(userId) as int64) is not null
      and safe_cast(trim(movieId) as int64) is not null
)

select
    user_id,
    movie_id,
    predicted_rating,
    coalesce(
        safe.parse_timestamp('%Y-%m-%d %H:%M:%S', raw_ts),
        timestamp_seconds(safe_cast(raw_ts as int64))
    ) as recommendation_ts
from raw_recs
where predicted_rating is not null

