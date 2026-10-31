# Guia de Publicação de Portfólio (GitHub + Streamlit Cloud + LinkedIn)

Este documento reúne o passo a passo enxuto para publicar o projeto com segurança máxima (zero credenciais expostas), colocar o **Data App ao vivo na internet gratuitamente** e apresentar os resultados técnicos no LinkedIn.

---

## 1. Publicar o Repositório no GitHub (`LuciannErlan`)

O repositório Git local (`branch main`) já está inicializado, auditado pelo `.gitignore` (ignorando `.env`, `secrets/`, `.venv/` e os CSVs/Parquets brutos pesados) e com o commit estruturado pronto.

1. Acesse https://github.com/new e crie um repositório **Público** sem marcar *Add a README* (por exemplo: `engenharia-de-dados-netflix`).
2. No terminal do projeto, conecte o repositório remoto e envie o código:

```powershell
git remote add origin https://github.com/LuciannErlan/engenharia-de-dados-netflix.git
git push -u origin main
```

Assim que o `git push` terminar, a aba **Actions** do GitHub executará automaticamente o workflow `.github/workflows/ci.yml` (`Ruff` + `Pytest` + `dbt parse`), exibindo o selo verde de CI aprovado!

---

## 2. Colocar o Dashboard Interativo no Ar (Streamlit Community Cloud — R$ 0)

Como exportamos as 8 views agregadas da camada Gold em `data/gold_cache/*.parquet` (~205 KB totais em Apache Arrow ZSTD), o dashboard roda na nuvem em milissegundos **sem precisar expor nenhuma chave do Google Cloud**:

1. Acesse https://share.streamlit.io/ e entre com sua conta do GitHub.
2. Clique em **Create app** → **Deploy a public app from GitHub**.
3. Preencha os campos:
   - **Repository**: `LuciannErlan/engenharia-de-dados-netflix`
   - **Branch**: `main`
   - **Main file path**: `dashboard/app.py`
4. Clique em **Deploy!**. Em cerca de 1 minuto você terá uma URL pública (`https://...streamlit.app`) para fixar na seção *About* do GitHub e no seu post do LinkedIn!

---

## 3. Capturas Visuais Recomendadas (GIF / Prints para LinkedIn)

Antes de publicar seu post, grave um vídeo curto (30–45s) ou tire 3 a 4 prints mostrando:
1. **Streamlit Data App (`http://localhost:8501`)**: alternância entre **Dark Mode / Light Mode**, o *Heatmap Sazonal*, o *Scatter Plot de Quadrantes* e a aba **Lab de Recomendação**.
2. **Dashboard Público do Metabase (`http://localhost:3000`)**: o painel executivo com os **9 Cards** consultando ao vivo o Google BigQuery (`netflix_analytics`).
3. **Execução Técnica**: print do terminal com `dbt run` (`PASS=22`) + `dbt test` (`PASS=48`) ou do selo verde do **GitHub Actions**.

---

## 4. Sugestão de Post para o LinkedIn (Pronto para Copiar e Adaptar)

> **Construí uma Plataforma Analítica End-to-End de Streaming & Sistemas de Recomendação processando +10,7 milhões de registros reais no Google BigQuery!** 🎬🚀
>
> Dando sequência à minha jornada prática em Engenharia de Dados, desenvolvi meu segundo projeto completo de portfólio modelando o dataset oficial **MovieLens Beliefs 2024** (*GroupLens Research*) — indo além da análise de catálogo para avaliar também a assertividade de algoritmos de recomendação frente à expectativa humana.
>
> 🔧 **Arquitetura & Decisões de Engenharia:**
> - **Ingestão Streaming & Compressão Colunar (`Python` + `PyArrow`)**: conversão em lotes de 6 arquivos CSV (**482,4 MB**) para **Apache Parquet ZSTD (101,8 MB)**, reduzindo **78,9%** do volume de armazenamento e transferência antes da carga no Data Warehouse.
> - **Data Warehouse (`Google BigQuery`)**: camada Bronze *schema-on-read* (`netflix_raw`) e camada analítica (`netflix_analytics`) otimizada com *Clustering* físico.
> - **Analytics Engineering (`dbt Core`)**: 22 modelos organizados em arquitetura Medallion + **Star Schema (Kimball)** (`dim_movies`, `dim_genres`, `bridge_movie_genres`, `dim_users`, `dim_date`, `fact_ratings` e `fact_beliefs`), protegidos por **48 testes automatizados** (`unique`, `not_null`, integridade referencial e *dbt unit tests*), deduplicando +828 mil avaliações sobrepostas.
> - **BI-as-Code & Visualização Dupla**: provisionamento automatizado de conexão segura (*Service Account least-privilege*), 9 *Questions* e Dashboard público no **Metabase + PostgreSQL 16 (Docker Compose)**, além de um **Data App interativo em Streamlit + Plotly** com suporte a Dark/Light Mode.
> - **Qualidade & CI/CD**: suíte de testes com `Pytest`, padronização com `Ruff` e integração contínua via **GitHub Actions**.
>
> 📊 **Um insight real de Produto & ML encontrado nos dados:**
> Ao cruzar expectativa prévia do usuário, predição do algoritmo (`MAE = 0,653 ★`) e nota real pós-consumo em +3 milhões de interações, descobrimos o **Paradoxo da Serendipidade**: recomendações fora da bolha recebem baixa expectativa inicial dos usuários (`2,16 ★` antes de assistir), mas atingem **`3,82 ★` de aprovação real** após o consumo — superando inclusive a nota prevista pelo próprio modelo (`3,54 ★`)!
>
> 🔗 **Repositório no GitHub:** https://github.com/LuciannErlan/engenharia-de-dados-netflix
> 🌐 **Data App Interativo (Streamlit):** [INSERIR LINK DO STREAMLIT CLOUD]
>
> *(Inspirado na aula base da Luiza Vieira / Dados Por Todos, expandido com Parquet colunar, dbt Core, testes automatizados, BI-as-Code e CI/CD.)*
>
> #EngenhariaDeDados #DataEngineering #AnalyticsEngineering #BigQuery #dbt #Python #ApacheParquet #Metabase #Streamlit #SQL #Portfolio

