{{
    config(
        materialized = "view"
    )
}}

-- Calibração do nível de confiança do usuário (1 a 5) frente às notas previstas e reais
select
    user_certainty,
    case user_certainty
        when 1 then '1 - Muito Incerto'
        when 2 then '2 - Pouco Certo'
        when 3 then '3 - Moderado'
        when 4 then '4 - Confiante'
        when 5 then '5 - Absoluta Certeza'
    end as certainty_label,
    count(*) as total_responses,
    round(avg(user_predict_rating), 3) as avg_expected_rating,
    round(avg(system_predict_rating), 3) as avg_algorithm_rating,
    round(avg(abs(user_predict_rating - system_predict_rating)), 3) as avg_human_algo_divergence
from {{ ref('fact_beliefs') }}
where user_certainty between 1 and 5
group by user_certainty

