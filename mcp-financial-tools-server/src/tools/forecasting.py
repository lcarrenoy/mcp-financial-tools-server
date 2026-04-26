"""Tools: analyze_cashflow, forecast_revenue, detect_anomalies"""
from datetime import datetime
from typing import List


# ── CASHFLOW ──────────────────────────────────────────────────────────────────
def analyze_cashflow(
    cash_beginning: float,
    operating_cashflow: float,
    investing_cashflow: float,
    financing_cashflow: float,
    capex: float = 0,
    monthly_burn_rate: float = None,
    projection_months: int = 12,
) -> dict:
    net_change = operating_cashflow + investing_cashflow + financing_cashflow
    cash_end = cash_beginning + net_change
    fcf = operating_cashflow - capex

    alerts = []
    if cash_end < 0:
        alerts.append("🔴 CRÍTICO: Posición de caja negativa al cierre del período")
    if fcf < 0:
        alerts.append("🟡 FCF negativo — la empresa consume más caja de la que genera operativamente")
    if operating_cashflow < 0:
        alerts.append("🔴 Flujo operativo negativo — core business no genera caja")

    runway = None
    if monthly_burn_rate and monthly_burn_rate > 0:
        runway = cash_end / monthly_burn_rate
        if runway < 6:
            alerts.append(f"🔴 CRÍTICO: Runway de solo {runway:.1f} meses")
        elif runway < 12:
            alerts.append(f"🟡 Runway ajustado: {runway:.1f} meses")

    projections = []
    monthly_op = operating_cashflow / 12
    monthly_invest = investing_cashflow / 12
    monthly_fin = financing_cashflow / 12
    running_cash = cash_end
    for m in range(1, projection_months + 1):
        running_cash += monthly_op + monthly_invest + monthly_fin
        projections.append({"month": m, "projected_cash": round(running_cash, 0)})
        if running_cash < 0 and not any("proyección" in a for a in alerts):
            alerts.append(f"⚠️ Proyección: caja negativa en mes {m} bajo tendencia actual")

    return {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "cash_beginning": cash_beginning,
            "operating_cashflow": operating_cashflow,
            "investing_cashflow": investing_cashflow,
            "financing_cashflow": financing_cashflow,
            "net_change": round(net_change, 0),
            "cash_ending": round(cash_end, 0),
            "free_cash_flow": round(fcf, 0),
            "runway_months": round(runway, 1) if runway else "N/A",
        },
        "cash_flow_quality": _cashflow_quality(operating_cashflow, net_change),
        "projections_monthly": projections[:6],
        "alerts": alerts if alerts else ["✅ Sin alertas de riesgo de liquidez"],
    }


def _cashflow_quality(operating_cf, net_change):
    if operating_cf > 0 and net_change > 0:
        return "✅ Excelente — flujo operativo positivo y caja creciente"
    if operating_cf > 0:
        return "🟡 Bueno — flujo operativo positivo pero inversiones/financiamiento consumen caja"
    return "🔴 Atención — negocio no genera caja operativa"


# ── FORECASTING ───────────────────────────────────────────────────────────────
def forecast_revenue(
    historical_data: List[dict],
    forecast_periods: int = 6,
    seasonality: bool = True,
) -> dict:
    if len(historical_data) < 3:
        return {"error": "Se necesitan al menos 3 puntos históricos para forecastear"}

    values = [d["revenue"] for d in historical_data]
    n = len(values)

    # Regresión lineal simple (OLS)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(values) / n
    slope = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values)) / \
            sum((xi - x_mean) ** 2 for xi in x)
    intercept = y_mean - slope * x_mean

    # Proyección
    forecasts = []
    last_date_parts = historical_data[-1]["date"].split("-")
    year, month = int(last_date_parts[0]), int(last_date_parts[1])

    for i in range(1, forecast_periods + 1):
        month += 1
        if month > 12:
            month = 1
            year += 1
        point = intercept + slope * (n + i - 1)
        seasonal_factor = 1.0
        if seasonality:
            seasonal_factors = {1: 0.92, 2: 0.95, 3: 1.02, 4: 1.05, 5: 1.08,
                                 6: 1.03, 7: 0.97, 8: 0.98, 9: 1.04, 10: 1.07,
                                 11: 1.12, 12: 1.18}
            seasonal_factor = seasonal_factors.get(month, 1.0)
        point_adj = max(0, point * seasonal_factor)
        ci_low = point_adj * 0.85
        ci_high = point_adj * 1.15
        forecasts.append({
            "date": f"{year}-{month:02d}",
            "forecast": round(point_adj, 0),
            "ci_low_85": round(ci_low, 0),
            "ci_high_85": round(ci_high, 0),
        })

    growth_rate = (slope / y_mean * 100) if y_mean else 0
    total_forecast = sum(f["forecast"] for f in forecasts)
    total_historical = sum(values[-forecast_periods:]) if len(values) >= forecast_periods else sum(values)

    return {
        "timestamp": datetime.now().isoformat(),
        "model": "linear_regression" + ("_with_seasonality" if seasonality else ""),
        "historical_periods": n,
        "avg_historical_revenue": round(y_mean, 0),
        "monthly_growth_rate_pct": round(growth_rate, 2),
        "forecast": forecasts,
        "summary": {
            "total_forecasted": round(total_forecast, 0),
            "vs_prior_same_periods": f"+{((total_forecast/total_historical)-1)*100:.1f}%"
            if total_historical > 0 else "N/A",
        },
        "caveats": [
            "Modelo de regresión lineal simple — para mayor precisión usar Prophet con datos >12 meses",
            "Intervalos de confianza al 85% — pueden variar significativamente ante eventos no lineales",
        ],
    }


# ── ANOMALY DETECTION ─────────────────────────────────────────────────────────
def detect_anomalies(
    time_series: List[dict],
    metric_name: str,
    method: str = "both",
    threshold: float = 2.5,
) -> dict:
    values = [d["value"] for d in time_series]
    n = len(values)
    if n < 4:
        return {"error": "Se necesitan al menos 4 puntos para detectar anomalías"}

    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    std = variance ** 0.5

    sorted_vals = sorted(values)
    q1 = sorted_vals[n // 4]
    q3 = sorted_vals[3 * n // 4]
    iqr = q3 - q1
    lower_iqr = q1 - 1.5 * iqr
    upper_iqr = q3 + 1.5 * iqr

    anomalies = []
    for point in time_series:
        v = point["value"]
        z = (v - mean) / std if std > 0 else 0
        is_zscore = abs(z) > threshold
        is_iqr = v < lower_iqr or v > upper_iqr
        flagged = (method == "zscore" and is_zscore) or \
                  (method == "iqr" and is_iqr) or \
                  (method == "both" and (is_zscore or is_iqr))
        if flagged:
            direction = "above" if v > mean else "below"
            severity = "HIGH" if abs(z) > threshold * 1.5 else "MEDIUM"
            anomalies.append({
                "date": point["date"],
                "value": v,
                "z_score": round(z, 2),
                "direction": direction,
                "deviation_from_mean_pct": round((v - mean) / mean * 100, 1) if mean else 0,
                "severity": severity,
                "detected_by": ("both" if (is_zscore and is_iqr) else
                                "zscore" if is_zscore else "iqr"),
            })

    anomalies.sort(key=lambda x: abs(x["z_score"]), reverse=True)
    return {
        "timestamp": datetime.now().isoformat(),
        "metric": metric_name,
        "method": method,
        "threshold": threshold,
        "statistics": {
            "n_points": n,
            "mean": round(mean, 2),
            "std": round(std, 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "iqr_range": [round(lower_iqr, 2), round(upper_iqr, 2)],
        },
        "anomalies_found": len(anomalies),
        "anomaly_rate_pct": round(len(anomalies) / n * 100, 1),
        "anomalies": anomalies,
        "assessment": (
            "✅ Sin anomalías detectadas — serie temporal consistente"
            if not anomalies else
            f"⚠️ {len(anomalies)} anomalía(s) detectada(s) — requiere revisión"
        ),
    }
