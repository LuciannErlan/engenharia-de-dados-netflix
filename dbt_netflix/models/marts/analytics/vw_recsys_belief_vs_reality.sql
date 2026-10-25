{{
    config(
        materialized = "view"
    )
}}

-- View Exclusiva de Portfólio: Avaliação do Motor de Recomendação vs. Expectativa Humana por Canal
select
    source_id,
    discovery_source,
    count(*) as total_impressions,
    countif(is_seen_code = 1) as watched_count,
    countif(is_seen_code = 0) as unseen_count,
    round(safe_divide(countif(is_seen_code = 1) * 100.0, nullif(countif(is_seen_code in (0, 1)), 0)), 2) as watch_conversion_pct,
    round(avg(user_predict_rating), 3) as avg_user_predicted_rating,
    round(avg(user_elicit_rating), 3) as avg_actual_watched_rating,
    round(avg(system_predict_rating), 3) as avg_system_predicted_rating,
    round(avg(expectation_surprise_gap), 3) as avg_surprise_gap,
    round(avg(system_abs_error), 3) as system_mae,
    round(avg(user_abs_error), 3) as user_expectation_mae
from {{ ref('fact_beliefs') }}
where source_id between 1 and 5
group by
    source_id,
    discovery_source

