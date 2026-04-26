"""
Tool: query_kpis
Simula consulta de KPIs desde base de datos (stub para demo).
En producción: conectar a BigQuery, Snowflake, o PostgreSQL.
"""
from datetime import datetime
import random


def query_kpis(
    company_id: str,
    period: str,
    kpi_category: str = "all",
    include_benchmark: bool = True,
) -> dict:
    """Consulta KPIs financieros. Stub con datos demo — reemplazar con DB real."""

    # En producción esto sería:
    # conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    # df = pd.read_sql(query, conn)

    base_kpis = {
        "revenue": {
            "total_revenue": {"value": 4_250_000, "unit": "USD", "vs_prior": "+12.3%"},
            "mrr": {"value": 354_167, "unit": "USD/month", "vs_prior": "+8.1%"},
            "arr": {"value": 4_250_000, "unit": "USD", "vs_prior": "+12.3%"},
            "revenue_growth_yoy": {"value": 12.3, "unit": "%"},
        },
        "profitability": {
            "gross_margin": {"value": 68.4, "unit": "%", "vs_prior": "+2.1pp"},
            "ebitda_margin": {"value": 22.7, "unit": "%", "vs_prior": "+1.8pp"},
            "net_margin": {"value": 14.2, "unit": "%", "vs_prior": "+0.9pp"},
            "burn_multiple": {"value": 1.4, "unit": "x", "vs_prior": "-0.3x"},
        },
        "liquidity": {
            "cash_position": {"value": 2_800_000, "unit": "USD"},
            "runway_months": {"value": 18, "unit": "months"},
            "current_ratio": {"value": 2.1, "unit": "x"},
            "quick_ratio": {"value": 1.8, "unit": "x"},
        },
        "operations": {
            "cac": {"value": 1_250, "unit": "USD/customer", "vs_prior": "-8.3%"},
            "ltv": {"value": 18_400, "unit": "USD/customer", "vs_prior": "+5.2%"},
            "ltv_cac_ratio": {"value": 14.7, "unit": "x", "vs_prior": "+1.9x"},
            "churn_rate": {"value": 2.1, "unit": "%/month", "vs_prior": "-0.4pp"},
            "nrr": {"value": 118, "unit": "%", "vs_prior": "+3pp"},
        },
    }

    sector_benchmarks = {
        "gross_margin": {"p25": 55, "median": 65, "p75": 75, "unit": "%"},
        "net_margin": {"p25": 8, "median": 14, "p75": 22, "unit": "%"},
        "ltv_cac_ratio": {"p25": 3, "median": 5, "p75": 10, "unit": "x"},
        "churn_rate": {"p25": 1.5, "median": 3, "p75": 5, "unit": "%/month"},
        "runway_months": {"p25": 12, "median": 18, "p75": 24, "unit": "months"},
    }

    if kpi_category == "all":
        selected_kpis = base_kpis
    else:
        selected_kpis = {kpi_category: base_kpis.get(kpi_category, {})}

    result = {
        "company_id": company_id,
        "period": period,
        "query_timestamp": datetime.now().isoformat(),
        "kpis": selected_kpis,
    }

    if include_benchmark:
        result["sector_benchmarks"] = sector_benchmarks
        result["benchmark_note"] = "Benchmarks basados en SaaS B2B — percentiles P25/P50/P75"

    return result
