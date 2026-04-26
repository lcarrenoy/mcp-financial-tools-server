"""
Tool: calculate_financial_ratios
Calcula ratios financieros clave desde estados financieros.
"""
from datetime import datetime


def calculate_financial_ratios(
    current_assets: float,
    current_liabilities: float,
    total_assets: float,
    total_equity: float,
    net_income: float,
    revenue: float,
    inventory: float = 0,
    total_debt: float = 0,
    ebit: float = None,
    interest_expense: float = 0,
) -> dict:
    """Calcula ratios de liquidez, rentabilidad y deuda."""

    results = {
        "timestamp": datetime.now().isoformat(),
        "input_summary": {
            "revenue_usd": revenue,
            "total_assets_usd": total_assets,
            "total_equity_usd": total_equity,
        },
    }

    # ── Ratios de Liquidez ────────────────────────────────────────────────────
    current_ratio = current_assets / current_liabilities if current_liabilities else None
    quick_ratio = (current_assets - inventory) / current_liabilities if current_liabilities else None

    results["liquidity"] = {
        "current_ratio": round(current_ratio, 3) if current_ratio else None,
        "quick_ratio": round(quick_ratio, 3) if quick_ratio else None,
        "interpretation": {
            "current_ratio": _interpret_current_ratio(current_ratio),
            "quick_ratio": _interpret_quick_ratio(quick_ratio),
        },
    }

    # ── Ratios de Rentabilidad ────────────────────────────────────────────────
    net_margin = (net_income / revenue * 100) if revenue else None
    roa = (net_income / total_assets * 100) if total_assets else None
    roe = (net_income / total_equity * 100) if total_equity else None

    results["profitability"] = {
        "net_margin_pct": round(net_margin, 2) if net_margin else None,
        "return_on_assets_pct": round(roa, 2) if roa else None,
        "return_on_equity_pct": round(roe, 2) if roe else None,
        "interpretation": {
            "net_margin": _interpret_margin(net_margin),
            "roe": _interpret_roe(roe),
        },
    }

    # ── Ratios de Deuda ───────────────────────────────────────────────────────
    de_ratio = (total_debt / total_equity) if total_equity and total_debt else None
    debt_to_assets = (total_debt / total_assets) if total_assets and total_debt else None

    if ebit is None:
        ebit = net_income * 1.3  # estimación aproximada si no se provee

    interest_coverage = (ebit / interest_expense) if interest_expense else None

    results["leverage"] = {
        "debt_to_equity": round(de_ratio, 3) if de_ratio else None,
        "debt_to_assets_pct": round(debt_to_assets * 100, 2) if debt_to_assets else None,
        "interest_coverage": round(interest_coverage, 2) if interest_coverage else "N/A (sin deuda)",
        "interpretation": {
            "de_ratio": _interpret_de_ratio(de_ratio),
            "interest_coverage": _interpret_coverage(interest_coverage),
        },
    }

    # ── Semáforo de Riesgo ────────────────────────────────────────────────────
    results["risk_traffic_light"] = _risk_traffic_light(
        current_ratio, net_margin, roe, de_ratio, interest_coverage
    )

    return results


def _interpret_current_ratio(ratio):
    if ratio is None:
        return "Sin datos"
    if ratio >= 2.0:
        return "✅ Excelente liquidez (>2.0)"
    if ratio >= 1.5:
        return "🟢 Buena liquidez (1.5-2.0)"
    if ratio >= 1.0:
        return "🟡 Liquidez ajustada (1.0-1.5)"
    return "🔴 Riesgo de liquidez (<1.0)"


def _interpret_quick_ratio(ratio):
    if ratio is None:
        return "Sin datos"
    if ratio >= 1.0:
        return "✅ Sin dependencia de inventario"
    if ratio >= 0.7:
        return "🟡 Dependencia moderada de inventario"
    return "🔴 Alta dependencia de inventario"


def _interpret_margin(margin):
    if margin is None:
        return "Sin datos"
    if margin >= 20:
        return "✅ Margen excelente (>20%)"
    if margin >= 10:
        return "🟢 Margen sano (10-20%)"
    if margin >= 5:
        return "🟡 Margen moderado (5-10%)"
    if margin >= 0:
        return "🟠 Margen bajo (0-5%)"
    return "🔴 Empresa en pérdida"


def _interpret_roe(roe):
    if roe is None:
        return "Sin datos"
    if roe >= 20:
        return "✅ ROE excepcional (>20%)"
    if roe >= 15:
        return "🟢 ROE bueno (15-20%)"
    if roe >= 10:
        return "🟡 ROE moderado (10-15%)"
    return "🔴 ROE bajo (<10%)"


def _interpret_de_ratio(ratio):
    if ratio is None:
        return "Sin deuda registrada"
    if ratio <= 0.5:
        return "✅ Apalancamiento conservador"
    if ratio <= 1.0:
        return "🟢 Apalancamiento moderado"
    if ratio <= 2.0:
        return "🟡 Apalancamiento elevado"
    return "🔴 Apalancamiento muy alto — riesgo"


def _interpret_coverage(ratio):
    if ratio is None:
        return "Sin deuda financiera"
    if ratio >= 5:
        return "✅ Excelente cobertura de intereses"
    if ratio >= 3:
        return "🟢 Cobertura adecuada"
    if ratio >= 1.5:
        return "🟡 Cobertura ajustada"
    return "🔴 Riesgo de impago de intereses"


def _risk_traffic_light(current_ratio, net_margin, roe, de_ratio, interest_coverage):
    """Genera un semáforo de riesgo consolidado (RED/YELLOW/GREEN)."""
    score = 0
    flags = []

    if current_ratio and current_ratio >= 1.5:
        score += 2
    elif current_ratio and current_ratio >= 1.0:
        score += 1
    else:
        flags.append("Liquidez comprometida")

    if net_margin and net_margin >= 10:
        score += 2
    elif net_margin and net_margin >= 0:
        score += 1
    else:
        flags.append("Empresa en pérdida")

    if roe and roe >= 15:
        score += 2
    elif roe and roe >= 10:
        score += 1
    else:
        flags.append("ROE bajo")

    if de_ratio is None or de_ratio <= 1.0:
        score += 2
    elif de_ratio <= 2.0:
        score += 1
    else:
        flags.append("Apalancamiento excesivo")

    if score >= 7:
        status = "GREEN"
        label = "✅ Perfil financiero sólido"
    elif score >= 4:
        status = "YELLOW"
        label = "🟡 Perfil financiero con riesgos moderados"
    else:
        status = "RED"
        label = "🔴 Perfil financiero de alto riesgo"

    return {"status": status, "label": label, "risk_flags": flags, "score": f"{score}/8"}
