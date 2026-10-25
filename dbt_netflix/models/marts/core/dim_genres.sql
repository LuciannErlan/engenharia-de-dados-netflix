{{
    config(
        materialized = "table",
        hours_to_expiration = var('sandbox_hours_to_expiration', 1400)
    )
}}

with distinct_genres as (
    select
        genre_name,
        count(distinct movie_id) as catalog_movies_count
    from {{ ref('int_movie_genres') }}
    group by genre_name
)

select
    to_hex(md5(genre_name)) as genre_sk,
    genre_name,
    catalog_movies_count
from distinct_genres

