{{
    config(
        materialized = "view"
    )
}}

-- View para Bar Charts: Top Filmes por Qualidade Ponderada (Bayesian Score) e Mais Avaliados (>= 50 avaliações)
select
    movie_id,
    title,
    clean_title,
    release_year,
    primary_genre,
    genres_list,
    total_ratings,
    unique_users,
    round(avg_rating, 3) as avg_rating,
    round(stddev_rating, 3) as stddev_rating,
    round(bayesian_weighted_score, 3) as weighted_score,
    dense_rank() over (order by bayesian_weighted_score desc, total_ratings desc) as quality_rank,
    dense_rank() over (order by total_ratings desc, avg_rating desc) as popularity_rank
from {{ ref('dim_movies') }}
where total_ratings >= 50

