{{
    config(
        materialized = "table",
        hours_to_expiration = var('sandbox_hours_to_expiration', 1400),
        cluster_by = ["activity_tier"]
    )
}}

with user_agg as (
    select
        user_id,
        count(*) as total_ratings,
        count(distinct movie_id) as unique_movies_rated,
        round(avg(rating), 4) as avg_rating,
        round(coalesce(stddev_samp(rating), 0.0), 4) as stddev_rating,
        min(rating_ts) as first_rating_ts,
        max(rating_ts) as last_rating_ts,
        date_diff(max(rating_date), min(rating_date), day) as active_days_span
    from {{ ref('stg_ratings') }}
    group by user_id
)

select
    user_id,
    total_ratings,
    unique_movies_rated,
    avg_rating,
    stddev_rating,
    first_rating_ts,
    last_rating_ts,
    active_days_span,
    case
        when total_ratings >= 500 then 'Power Reviewer (500+)'
        when total_ratings >= 100 then 'Heavy Watcher (100-499)'
        when total_ratings >= 20 then 'Engaged (20-99)'
        else 'Casual (<20)'
    end as activity_tier
from user_agg

