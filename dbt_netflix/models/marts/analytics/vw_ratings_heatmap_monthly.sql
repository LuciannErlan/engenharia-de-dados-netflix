{{
    config(
        materialized = "view"
    )
}}

-- View para Heatmap no Metabase / Streamlit: Evolução mensal de avaliações por ano
select
    rating_year,
    rating_month,
    format_date('%b', date(rating_year, rating_month, 1)) as month_label,
    format('%04d-%02d', rating_year, rating_month) as year_month,
    count(*) as total_ratings,
    count(distinct user_id) as active_users,
    count(distinct movie_id) as rated_movies,
    round(avg(rating), 3) as avg_rating
from {{ ref('fact_ratings') }}
group by
    rating_year,
    rating_month

