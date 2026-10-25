{{
    config(
        materialized = "table",
        hours_to_expiration = var('sandbox_hours_to_expiration', 1400)
    )
}}

with bounds as (
    select
        coalesce(min(rating_date), date('2000-01-01')) as min_date,
        coalesce(max(rating_date), date('2024-12-31')) as max_date
    from {{ ref('stg_ratings') }}
),

calendar as (
    select calendar_date
    from bounds,
    unnest(generate_date_array(min_date, max_date, interval 1 day)) as calendar_date
)

select
    cast(format_date('%Y%m%d', calendar_date) as int64) as date_key,
    calendar_date as full_date,
    extract(year from calendar_date) as year,
    extract(quarter from calendar_date) as quarter,
    extract(month from calendar_date) as month,
    format_date('%b', calendar_date) as month_short,
    format_date('%Y-%m', calendar_date) as year_month,
    extract(dayofweek from calendar_date) as day_of_week,
    format_date('%a', calendar_date) as day_name_short,
    extract(dayofweek from calendar_date) in (1, 7) as is_weekend
from calendar

