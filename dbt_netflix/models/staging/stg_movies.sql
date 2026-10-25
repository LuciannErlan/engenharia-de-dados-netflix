{{
    config(
        materialized = "view"
    )
}}

-- Camada Bronze/Staging: Limpeza, deduplicação, extração de ano via Regex e tratamento de array de gêneros
with raw_movies as (
    select
        safe_cast(trim(movieId) as int64) as movie_id,
        trim(title) as raw_title,
        trim(genres) as genres_raw,
        _ingested_at
    from {{ source('netflix_raw', 'movies') }}
    where safe_cast(trim(movieId) as int64) is not null
),

deduplicated as (
    select
        movie_id,
        raw_title,
        genres_raw,
        _ingested_at
    from raw_movies
    qualify row_number() over (partition by movie_id order by _ingested_at desc) = 1
),

cleaned as (
    select
        movie_id,
        raw_title as title,
        coalesce(
            nullif(trim(regexp_replace(raw_title, r'\s*\(\d{4}\)\s*$', '')), ''),
            raw_title
        ) as clean_title,
        safe_cast(regexp_extract(raw_title, r'\((\d{4})\)\s*$') as int64) as release_year,
        case
            when genres_raw is null or genres_raw = '' or lower(genres_raw) = '(no genres listed)'
                then null
            else genres_raw
        end as genres_raw,
        array(
            select distinct trim(genre_item)
            from unnest(split(coalesce(genres_raw, ''), '|')) as genre_item
            where trim(genre_item) != ''
              and lower(trim(genre_item)) != '(no genres listed)'
        ) as genres_array
    from deduplicated
)

select
    movie_id,
    title,
    clean_title,
    release_year,
    cast(floor(release_year / 10) * 10 as int64) as release_decade,
    genres_raw,
    genres_array,
    coalesce(genres_array[safe_offset(0)], 'Unclassified') as primary_genre,
    array_length(genres_array) = 0 as is_no_genre
from cleaned

