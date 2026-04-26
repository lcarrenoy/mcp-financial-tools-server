"""
MCP Financial Tools Server
==========================
Servidor MCP que expone herramientas financieras como tools para agentes LLM.
Implementa el Model Context Protocol (MCP) de Anthropic.

Tools expuestas:
  - calculate_financial_ratios   → ratios de liquidez, rentabilidad, deuda
  - query_kpis                   → consulta KPIs desde base de datos
  - analyze_cashflow             → análisis de flujo de caja
  - forecast_revenue             → forecast simple de revenue
  - detect_anomalies             → detección de anomalías en series temporales

Uso:
  uv run python src/server/main.py
  # O con Claude Desktop: configura en claude_desktop_config.json
"""

import asyncio
import json
import logging
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

from src.tools.financial_ratios import calculate_financial_ratios
from src.tools.kpi_query import query_kpis
from src.tools.cashflow import analyze_cashflow
from src.tools.forecasting import forecast_revenue
from src.tools.anomaly_detection import detect_anomalies

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-financial-server")

# ── Inicializar servidor MCP ──────────────────────────────────────────────────
server = Server("financial-tools-server")


@server.list_tools()
async def list_tools() -> ListToolsResult:
    """Registra todas las tools disponibles en el servidor MCP."""
    return ListToolsResult(
        tools=[
            Tool(
                name="calculate_financial_ratios",
                description=(
                    "Calcula ratios financieros clave a partir de estados financieros. "
                    "Incluye ratios de liquidez (current ratio, quick ratio), "
                    "rentabilidad (ROE, ROA, margen neto), y deuda (D/E ratio, interest coverage). "
                    "Útil para análisis crediticio y valuación de empresas."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "current_assets": {"type": "number", "description": "Activos corrientes (USD)"},
                        "current_liabilities": {"type": "number", "description": "Pasivos corrientes (USD)"},
                        "inventory": {"type": "number", "description": "Inventarios (USD)"},
                        "total_assets": {"type": "number", "description": "Total activos (USD)"},
                        "total_equity": {"type": "number", "description": "Patrimonio total (USD)"},
                        "total_debt": {"type": "number", "description": "Deuda total (USD)"},
                        "net_income": {"type": "number", "description": "Utilidad neta (USD)"},
                        "revenue": {"type": "number", "description": "Revenue total (USD)"},
                        "ebit": {"type": "number", "description": "EBIT - Earnings Before Interest and Taxes (USD)"},
                        "interest_expense": {"type": "number", "description": "Gastos financieros (USD)"},
                    },
                    "required": ["current_assets", "current_liabilities", "total_assets", "total_equity", "net_income", "revenue"],
                },
            ),
            Tool(
                name="query_kpis",
                description=(
                    "Consulta KPIs financieros y operacionales desde la base de datos. "
                    "Permite filtrar por empresa, período, y categoría de KPI. "
                    "Retorna valores actuales, variación vs período anterior, y benchmarks del sector."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "company_id": {"type": "string", "description": "ID o nombre de la empresa"},
                        "period": {
                            "type": "string",
                            "description": "Período (e.g. '2024-Q4', '2024-12', 'YTD-2024')",
                        },
                        "kpi_category": {
                            "type": "string",
                            "enum": ["revenue", "profitability", "liquidity", "operations", "all"],
                            "description": "Categoría de KPIs a consultar",
                        },
                        "include_benchmark": {
                            "type": "boolean",
                            "description": "Incluir benchmark del sector (default: true)",
                        },
                    },
                    "required": ["company_id", "period"],
                },
            ),
            Tool(
                name="analyze_cashflow",
                description=(
                    "Analiza el flujo de caja de una empresa. "
                    "Calcula FCF (Free Cash Flow), runway, burn rate, y proyecciones de liquidez. "
                    "Genera alertas si detecta riesgo de insolvencia en los próximos N meses."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cash_beginning": {"type": "number", "description": "Caja inicial del período (USD)"},
                        "operating_cashflow": {"type": "number", "description": "Flujo operativo (USD)"},
                        "investing_cashflow": {"type": "number", "description": "Flujo de inversión (USD)"},
                        "financing_cashflow": {"type": "number", "description": "Flujo de financiamiento (USD)"},
                        "capex": {"type": "number", "description": "Capital expenditure (USD)"},
                        "monthly_burn_rate": {"type": "number", "description": "Burn rate mensual (USD, para startups)"},
                        "projection_months": {
                            "type": "integer",
                            "description": "Meses a proyectar (default: 12)",
                            "default": 12,
                        },
                    },
                    "required": ["cash_beginning", "operating_cashflow", "investing_cashflow", "financing_cashflow"],
                },
            ),
            Tool(
                name="forecast_revenue",
                description=(
                    "Genera forecast de revenue usando Prophet + regresión lineal simple. "
                    "Acepta serie histórica de revenue y retorna proyección con intervalos de confianza. "
                    "Útil para planning financiero y presupuestación."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "historical_data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "date": {"type": "string", "description": "Fecha YYYY-MM"},
                                    "revenue": {"type": "number", "description": "Revenue del período"},
                                },
                                "required": ["date", "revenue"],
                            },
                            "description": "Serie histórica de revenue (mínimo 6 puntos)",
                        },
                        "forecast_periods": {
                            "type": "integer",
                            "description": "Períodos a forecastear (default: 6)",
                            "default": 6,
                        },
                        "seasonality": {
                            "type": "boolean",
                            "description": "Considerar estacionalidad (default: true)",
                            "default": True,
                        },
                    },
                    "required": ["historical_data"],
                },
            ),
            Tool(
                name="detect_anomalies",
                description=(
                    "Detecta anomalías en series temporales financieras usando Z-score e IQR. "
                    "Útil para identificar fraudes, errores contables, o eventos inusuales en P&L, "
                    "flujo de caja, o cualquier métrica financiera."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "time_series": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "date": {"type": "string"},
                                    "value": {"type": "number"},
                                },
                                "required": ["date", "value"],
                            },
                            "description": "Serie temporal a analizar",
                        },
                        "metric_name": {"type": "string", "description": "Nombre de la métrica (para el reporte)"},
                        "method": {
                            "type": "string",
                            "enum": ["zscore", "iqr", "both"],
                            "description": "Método de detección (default: both)",
                            "default": "both",
                        },
                        "threshold": {
                            "type": "number",
                            "description": "Umbral de sensibilidad Z-score (default: 2.5)",
                            "default": 2.5,
                        },
                    },
                    "required": ["time_series", "metric_name"],
                },
            ),
        ]
    )


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """Dispatcher principal — enruta cada tool call a su implementación."""
    logger.info(f"Tool llamada: {name} | Args: {json.dumps(arguments, default=str)[:200]}")

    try:
        if name == "calculate_financial_ratios":
            result = calculate_financial_ratios(**arguments)

        elif name == "query_kpis":
            result = query_kpis(**arguments)

        elif name == "analyze_cashflow":
            result = analyze_cashflow(**arguments)

        elif name == "forecast_revenue":
            result = forecast_revenue(**arguments)

        elif name == "detect_anomalies":
            result = detect_anomalies(**arguments)

        else:
            raise ValueError(f"Tool desconocida: {name}")

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str),
                )
            ]
        )

    except Exception as e:
        logger.error(f"Error en tool {name}: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({"error": str(e), "tool": name, "timestamp": datetime.now().isoformat()}),
                )
            ],
            isError=True,
        )


async def main():
    logger.info("🚀 MCP Financial Tools Server iniciando...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
