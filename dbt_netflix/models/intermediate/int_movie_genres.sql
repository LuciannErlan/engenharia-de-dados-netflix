{{
    config(
        materialized = "view"
    )
}}

-- Camada Silver/Intermediate: Explosão normalizada do relacionamento N:N entre filmes e gêneros
with movies as (
    select
        movie_id,
        genres_array,
        is_no_genre
    from {{ ref('stg_movies') }}
),

exploded as (
    select
        m.movie_id,
        genre_name,
        genre_pos + 1 as genre_order
    from movies as m
    cross join unnest(m.genres_array) as genre_name with offset as genre_pos
    where not m.is_no_genre

    union all

    select
        m.movie_id,
        'Unclassified' as genre_name,
        1 as genre_order
    from movies as m
    where m.is_no_genre
)

select
    movie_id,
    genre_name,
    genre_order
from exploded

