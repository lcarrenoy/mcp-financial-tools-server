"""
Tests funcionales — MCP Financial Tools Server
Ejecutar: uv run python tests/test_tools.py
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.tools.financial_ratios import calculate_financial_ratios
from src.tools.kpi_query import query_kpis
from src.tools.cashflow import analyze_cashflow, forecast_revenue, detect_anomalies


def test_financial_ratios():
    print("\n" + "="*60)
    print("TEST: calculate_financial_ratios")
    print("="*60)
    result = calculate_financial_ratios(
        current_assets=5_000_000,
        current_liabilities=2_000_000,
        inventory=800_000,
        total_assets=12_000_000,
        total_equity=7_000_000,
        total_debt=3_500_000,
        net_income=1_200_000,
        revenue=8_500_000,
        ebit=1_800_000,
        interest_expense=350_000,
    )
    print(json.dumps(result, indent=2))
    assert result["risk_traffic_light"]["status"] in ["GREEN", "YELLOW", "RED"]
    print("✅ PASS")


def test_kpi_query():
    print("\n" + "="*60)
    print("TEST: query_kpis")
    print("="*60)
    result = query_kpis(
        company_id="YUMMY-001",
        period="2024-Q4",
        kpi_category="profitability",
        include_benchmark=True,
    )
    print(json.dumps(result, indent=2))
    assert "kpis" in result
    print("✅ PASS")


def test_cashflow():
    print("\n" + "="*60)
    print("TEST: analyze_cashflow")
    print("="*60)
    result = analyze_cashflow(
        cash_beginning=3_000_000,
        operating_cashflow=800_000,
        investing_cashflow=-1_200_000,
        financing_cashflow=500_000,
        capex=300_000,
        monthly_burn_rate=150_000,
        projection_months=6,
    )
    print(json.dumps(result, indent=2))
    assert "summary" in result
    print("✅ PASS")


def test_forecast():
    print("\n" + "="*60)
    print("TEST: forecast_revenue")
    print("="*60)
    historical = [
        {"date": "2024-01", "revenue": 320_000},
        {"date": "2024-02", "revenue": 335_000},
        {"date": "2024-03", "revenue": 358_000},
        {"date": "2024-04", "revenue": 372_000},
        {"date": "2024-05", "revenue": 391_000},
        {"date": "2024-06", "revenue": 385_000},
        {"date": "2024-07", "revenue": 402_000},
        {"date": "2024-08", "revenue": 418_000},
        {"date": "2024-09", "revenue": 435_000},
        {"date": "2024-10", "revenue": 451_000},
        {"date": "2024-11", "revenue": 478_000},
        {"date": "2024-12", "revenue": 512_000},
    ]
    result = forecast_revenue(historical, forecast_periods=6, seasonality=True)
    print(json.dumps(result, indent=2))
    assert len(result["forecast"]) == 6
    print("✅ PASS")


def test_anomalies():
    print("\n" + "="*60)
    print("TEST: detect_anomalies")
    print("="*60)
    # Serie con una anomalía evidente en julio
    series = [
        {"date": "2024-01", "value": 320_000},
        {"date": "2024-02", "value": 335_000},
        {"date": "2024-03", "value": 328_000},
        {"date": "2024-04", "value": 342_000},
        {"date": "2024-05", "value": 338_000},
        {"date": "2024-06", "value": 351_000},
        {"date": "2024-07", "value": 89_000},   # ← anomalía
        {"date": "2024-08", "value": 355_000},
        {"date": "2024-09", "value": 368_000},
        {"date": "2024-10", "value": 372_000},
    ]
    result = detect_anomalies(series, metric_name="monthly_revenue", method="both", threshold=2.0)
    print(json.dumps(result, indent=2))
    assert result["anomalies_found"] >= 1, "Debería detectar la anomalía de julio"
    print("✅ PASS — Anomalía detectada en julio como se esperaba")


if __name__ == "__main__":
    print("🧪 MCP Financial Tools — Test Suite")
    print("="*60)
    try:
        test_financial_ratios()
        test_kpi_query()
        test_cashflow()
        test_forecast()
        test_anomalies()
        print("\n" + "="*60)
        print("🎉 TODOS LOS TESTS PASARON")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
