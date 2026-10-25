{{
    config(
        materialized = "view"
    )
}}

-- Camada Silver/Intermediate: Early Aggregation de popularidade, média e desvio padrão por filme
select
    movie_id,
    count(*) as total_ratings,
    count(distinct user_id) as unique_users,
    round(avg(rating), 4) as avg_rating,
    round(coalesce(stddev_samp(rating), 0.0), 4) as stddev_rating,
    min(rating) as min_rating,
    max(rating) as max_rating,
    min(rating_date) as first_rating_date,
    max(rating_date) as last_rating_date
from {{ ref('stg_ratings') }}
group by movie_id

