-- =============================================================================
-- GUIA DE CONSULTAS SQL PARA O METABASE (http://localhost:3000)
-- Projeto GCP: netflix-analytics-de | Dataset: netflix_analytics
-- =============================================================================

-- 1. Evolução de Ratings ao Longo do Tempo (Visual: Heatmap / Tabela Dinâmica)
SELECT
    rating_year,
    month_label,
    rating_month,
    total_ratings,
    avg_rating
FROM `netflix-analytics-de.netflix_analytics.vw_ratings_heatmap_monthly`
WHERE rating_year >= 2010
ORDER BY rating_year, rating_month;

-- 2. Ranking de Filmes - Top 10 Melhor Avaliados (Visual: Bar Chart)
SELECT
    clean_title AS filme,
    release_year AS ano,
    primary_genre AS genero,
    weighted_score AS score_bayesiano,
    avg_rating AS nota_media,
    total_ratings AS total_avaliacoes
FROM `netflix-analytics-de.netflix_analytics.vw_top_movies_ranking`
WHERE total_ratings >= 100
ORDER BY weighted_score DESC
LIMIT 10;

-- 3. Filmes Mais Avaliados - Top 10 Popularidade (Visual: Bar Chart)
SELECT
    clean_title AS filme,
    total_ratings AS total_avaliacoes,
    avg_rating AS nota_media
FROM `netflix-analytics-de.netflix_analytics.vw_top_movies_ranking`
ORDER BY total_ratings DESC
LIMIT 10;

-- 4. Popularidade dos Gêneros (Visual: Bar Chart)
SELECT
    genre_name AS genero,
    total_ratings AS total_avaliacoes,
    total_movies AS qtd_filmes,
    avg_rating AS nota_media
FROM `netflix-analytics-de.netflix_analytics.vw_genre_popularity_quality`
ORDER BY total_ratings DESC;

-- 5. Atividade de Usuários (Visual: Table)
SELECT
    user_id,
    activity_tier,
    total_ratings,
    avg_rating,
    stddev_rating,
    first_rating_date,
    last_rating_date,
    active_days_span
FROM `netflix-analytics-de.netflix_analytics.vw_user_activity_summary`
ORDER BY total_ratings DESC
LIMIT 100;

-- 6. Filmes: Popularidade vs. Qualidade (Visual: Scatter Plot)
SELECT
    title,
    primary_genre,
    total_ratings,
    avg_rating,
    stddev_rating,
    quadrant_label
FROM `netflix-analytics-de.netflix_analytics.vw_movies_popularity_vs_quality`
WHERE total_ratings >= 100
ORDER BY total_ratings DESC
LIMIT 1000;

-- 7. Gênero: Popularidade vs. Qualidade (Visual: Scatter Plot)
SELECT
    genre_name,
    total_ratings,
    avg_rating,
    total_movies,
    stddev_rating
FROM `netflix-analytics-de.netflix_analytics.vw_genre_popularity_quality`;

-- 8. [BÔNUS PORTFÓLIO] Motor de Recomendação: Expectativa vs. Realidade
SELECT
    discovery_source,
    total_impressions,
    watch_conversion_pct,
    avg_user_predicted_rating,
    avg_system_predicted_rating,
    avg_actual_watched_rating,
    avg_surprise_gap,
    system_mae
FROM `netflix-analytics-de.netflix_analytics.vw_recsys_belief_vs_reality`
ORDER BY source_id;

