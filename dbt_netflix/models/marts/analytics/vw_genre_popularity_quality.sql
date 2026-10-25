{{
    config(
        materialized = "view"
    )
}}

-- View para Bar Chart e Scatter Plot de Gêneros: Popularidade vs. Qualidade e Desvio Padrão
select
    b.genre_name,
    count(distinct b.movie_id) as total_movies,
    count(f.rating_sk) as total_ratings,
    count(distinct f.user_id) as unique_users,
    round(avg(f.rating), 3) as avg_rating,
    round(coalesce(stddev_samp(f.rating), 0.0), 3) as stddev_rating,
    round(count(f.rating_sk) / nullif(count(distinct b.movie_id), 0), 1) as ratings_per_movie
from {{ ref('bridge_movie_genres') }} as b
inner join {{ ref('fact_ratings') }} as f
    on b.movie_id = f.movie_id
where b.genre_name != 'Unclassified'
group by b.genre_name

