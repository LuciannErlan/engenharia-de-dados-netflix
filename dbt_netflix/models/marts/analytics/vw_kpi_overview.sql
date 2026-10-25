{{
    config(
        materialized = "view"
    )
}}

with movie_counts as (
    select
        count(*) as total_catalog_movies,
        countif(total_ratings > 0) as rated_movies_count
    from {{ ref('dim_movies') }}
),

rating_stats as (
    select
        count(*) as total_ratings,
        count(distinct user_id) as total_active_users,
        round(avg(rating), 3) as global_avg_rating,
        round(stddev_samp(rating), 3) as global_stddev_rating,
        min(rating_date) as min_rating_date,
        max(rating_date) as max_rating_date
    from {{ ref('fact_ratings') }}
),

belief_stats as (
    select
        count(*) as total_belief_records,
        countif(is_seen_code = 1 and user_elicit_rating is not null) as verified_watch_beliefs,
        round(avg(system_abs_error), 3) as global_system_mae,
        round(avg(user_abs_error), 3) as global_user_mae
    from {{ ref('fact_beliefs') }}
)

select
    mc.total_catalog_movies,
    mc.rated_movies_count,
    rs.total_ratings,
    rs.total_active_users,
    rs.global_avg_rating,
    rs.global_stddev_rating,
    rs.min_rating_date,
    rs.max_rating_date,
    bs.total_belief_records,
    bs.verified_watch_beliefs,
    bs.global_system_mae,
    bs.global_user_mae
from movie_counts as mc
cross join rating_stats as rs
cross join belief_stats as bs

