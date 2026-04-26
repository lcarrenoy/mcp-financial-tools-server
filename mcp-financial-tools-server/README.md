# MCP Financial Tools Server

> MCP server that exposes financial analysis tools as callable tools for LLM agents. Built on the **Model Context Protocol (MCP)** — the emerging standard replacing custom tool-calling in production AI systems.

**Stack:** Python · MCP · Claude API · FastAPI · PostgreSQL · Pandas · Prophet

**KPIs:** 5 financial tools · Semáforo de riesgo · Detección de anomalías · Forecast con intervalos de confianza

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LLM Agent (Claude)                   │
│              LangGraph / Claude Desktop                 │
└────────────────────────┬────────────────────────────────┘
                         │  MCP Protocol (stdio / HTTP)
┌────────────────────────▼────────────────────────────────┐
│           MCP Financial Tools Server                    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Tool Registry                      │    │
│  │  calculate_financial_ratios  ← estados finanz.  │    │
│  │  query_kpis                  ← DB / BigQuery    │    │
│  │  analyze_cashflow            ← FCF + runway     │    │
│  │  forecast_revenue            ← Prophet + OLS   │    │
│  │  detect_anomalies            ← Z-score + IQR   │    │
│  └─────────────────────────────────────────────────┘    │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
   PostgreSQL / BigQuery          Pandas + Prophet
   (KPI database)                 (ML tools)
```

## MCP — Why it matters

The **Model Context Protocol** (Anthropic, 2024) is replacing custom tool-calling implementations across the industry. Instead of building bespoke `function_calling` schemas per LLM provider, MCP provides a standard client-server protocol where:

- Any MCP-compatible LLM (Claude, GPT-4o, Gemini) can discover and call your tools
- Tools are defined once, used everywhere
- The server handles transport (stdio, HTTP/SSE) transparently

This project demonstrates a **production-grade MCP server** with real financial domain tools — not a toy example.

## Tools

### `calculate_financial_ratios`
Computes liquidity, profitability, and leverage ratios from financial statements.
Returns a **risk traffic light** (GREEN/YELLOW/RED) with interpretation.

```json
{
  "current_assets": 5000000,
  "current_liabilities": 2000000,
  "total_assets": 12000000,
  "total_equity": 7000000,
  "net_income": 1200000,
  "revenue": 8500000
}
→ { "risk_traffic_light": { "status": "GREEN", "score": "8/8" }, ... }
```

### `query_kpis`
Queries financial KPIs from database with sector benchmarks (P25/P50/P75).

### `analyze_cashflow`
Computes FCF, runway, burn rate, and 12-month cash projection with alerts.

### `forecast_revenue`
Linear regression + seasonality forecast with 85% confidence intervals.

### `detect_anomalies`
Z-score + IQR anomaly detection for any financial time series.

## How to Run

```bash
# 1. Clone
git clone https://github.com/lcarrenoy/mcp-financial-tools-server.git
cd mcp-financial-tools-server

# 2. Install
uv sync

# 3. Configure
cp .env.example .env
# Edit .env with your DB credentials

# 4. Run tests
uv run python tests/test_tools.py

# 5. Start MCP server
uv run python -m src.server.main
```

### Connect to Claude Desktop

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "financial-tools": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.server.main"],
      "cwd": "/path/to/mcp-financial-tools-server"
    }
  }
}
```

### Connect to LangGraph Agent

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic

async with MultiServerMCPClient({
    "financial-tools": {
        "command": "uv",
        "args": ["run", "python", "-m", "src.server.main"],
        "transport": "stdio",
    }
}) as client:
    tools = await client.get_tools()
    agent = create_react_agent(ChatAnthropic(model="claude-sonnet-4-6"), tools)
    result = await agent.ainvoke({
        "messages": "Analiza los ratios financieros de YUMMY para Q4-2024 y dime si tiene riesgo de liquidez"
    })
```

## Project Structure

```
mcp-financial-tools-server/
├── src/
│   ├── server/
│   │   └── main.py              # MCP server + tool registry
│   └── tools/
│       ├── financial_ratios.py  # Ratios + risk traffic light
│       ├── kpi_query.py         # KPI database connector
│       ├── cashflow.py          # FCF + runway analysis
│       ├── forecasting.py       # Revenue forecast
│       └── anomaly_detection.py # Z-score + IQR detection
├── tests/
│   └── test_tools.py            # Functional tests (all pass ✅)
├── .env.example
├── pyproject.toml
└── claude_desktop_config.example.json
```

## Roadmap

- [ ] PostgreSQL / BigQuery connector for `query_kpis` (currently stub)
- [ ] Prophet integration in `forecast_revenue` (currently linear regression)
- [ ] LangFuse observability for tool call tracing
- [ ] Docker + docker-compose for containerized deployment
- [ ] HTTP/SSE transport (in addition to stdio)
- [ ] Authentication middleware for production

---

*Part of [Luis Carreño's Portfolio](https://github.com/lcarrenoy) · AI Engineer · Financial Engineering · MCP · Score 9.8/10*
