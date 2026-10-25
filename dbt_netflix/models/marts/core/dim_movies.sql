{{
    config(
        materialized = "table",
        hours_to_expiration = var('sandbox_hours_to_expiration', 1400),
        cluster_by = ["primary_genre", "release_year"]
    )
}}

-- Dimensão Gold de Filmes enriquecida com métricas agregadas e Weighted Rating Bayesiano (estilo IMDb/Netflix)
with movies as (
    select
        movie_id,
        title,
        clean_title,
        release_year,
        release_decade,
        genres_raw,
        primary_genre,
        is_no_genre
    from {{ ref('stg_movies') }}
),

metrics as (
    select
        movie_id,
        total_ratings,
        unique_users,
        avg_rating,
        stddev_rating,
        first_rating_date,
        last_rating_date
    from {{ ref('int_movie_metrics') }}
),

global_stats as (
    select
        coalesce(sum(total_ratings * avg_rating) / nullif(sum(total_ratings), 0), 3.5) as global_mean_rating,
        50.0 as min_votes_threshold
    from metrics
)

select
    m.movie_id,
    m.title,
    m.clean_title,
    m.release_year,
    m.release_decade,
    coalesce(m.genres_raw, 'Unclassified') as genres_list,
    m.primary_genre,
    m.is_no_genre,
    coalesce(mt.total_ratings, 0) as total_ratings,
    coalesce(mt.unique_users, 0) as unique_users,
    mt.avg_rating,
    mt.stddev_rating,
    case
        when coalesce(mt.total_ratings, 0) > 0 then round(
            (
                (mt.total_ratings / (mt.total_ratings + gs.min_votes_threshold)) * mt.avg_rating
            ) + (
                (gs.min_votes_threshold / (mt.total_ratings + gs.min_votes_threshold)) * gs.global_mean_rating
            ),
            4
        )
    end as bayesian_weighted_score,
    mt.first_rating_date,
    mt.last_rating_date
from movies as m
left join metrics as mt
    on m.movie_id = mt.movie_id
cross join global_stats as gs

