{{
    config(
        materialized = "table",
        hours_to_expiration = var('sandbox_hours_to_expiration', 1400),
        cluster_by = ["genre_name", "movie_id"]
    )
}}

select
    to_hex(md5(concat(cast(movie_id as string), '|', genre_name))) as movie_genre_sk,
    movie_id,
    to_hex(md5(genre_name)) as genre_sk,
    genre_name,
    genre_order
from {{ ref('int_movie_genres') }}

