{{
    config(
        materialized = "view"
    )
}}

-- View para Scatter Plot de Filmes: Popularidade vs. Qualidade com quadrantes analíticos da aula
with rated_movies as (
    select
        movie_id,
        title,
        clean_title,
        release_year,
        primary_genre,
        genres_list,
        total_ratings,
        round(avg_rating, 3) as avg_rating,
        round(stddev_rating, 3) as stddev_rating,
        round(bayesian_weighted_score, 3) as weighted_score
    from {{ ref('dim_movies') }}
    where total_ratings >= 20
),

thresholds as (
    select
        approx_quantiles(total_ratings, 100)[offset(75)] as pop_p75,
        round(avg(avg_rating), 3) as mean_quality
    from rated_movies
)

select
    rm.movie_id,
    rm.title,
    rm.clean_title,
    rm.release_year,
    rm.primary_genre,
    rm.genres_list,
    rm.total_ratings,
    rm.avg_rating,
    rm.stddev_rating,
    rm.weighted_score,
    case
        when rm.total_ratings >= t.pop_p75 and rm.avg_rating >= t.mean_quality
            then 'Muito Popular + Bem Avaliado'
        when rm.total_ratings < t.pop_p75 and rm.avg_rating >= t.mean_quality
            then 'Joia Cult (Bem Avaliado, Menos Popular)'
        when rm.total_ratings >= t.pop_p75 and rm.avg_rating < t.mean_quality
            then 'Popular com Nota Abaixo da Média'
        else 'Baixa Popularidade + Nota Baixa'
    end as quadrant_label
from rated_movies as rm
cross join thresholds as t

