# Wealth Advisor Assistant

A lightweight multi-agent system that simulates a Wealth Advisor Assistant. It ingests
client financial data, fetches additional context from (mock) external APIs, performs
financial analysis with anomaly detection, and produces a structured advisory report.

Built with **Python** and **LangGraph**. No LLM is required to run it — the "agents"
are deterministic units that share a typed state graph.

---

## 1. Architecture Design

The system is layered into four concerns, each in its own package:

```
wealth_advisor/
├── models.py            # Pydantic data models (transactions, accounts, anomalies, advisory)
├── state.py             # AdvisorState — the shared state that flows through the graph
├── logging_setup.py     # Centralized logging configuration
├── tools/               # Tool abstraction layer
│   ├── base.py          # Tool (ABC), ToolResult, ToolRegistry
│   ├── crm.py           # Mock CRM API tool
│   └── market_data.py   # Mock market data API tool
├── agents/              # Specialized agents
│   ├── base.py          # BaseAgent (ABC)
│   ├── orchestrator.py  # Central coordinator / router
│   ├── data_fetcher.py  # Ingests data + calls external tools
│   ├── analyzer.py      # Financial analysis + anomaly detection
│   └── advisor.py       # Produces structured advisory output
├── graph.py             # LangGraph state graph (wires agents together)
└── main.py              # CLI entry point
```

### Tool Usage Abstraction

Agents never import or call a raw API implementation. They depend on the `ToolRegistry`
and the `Tool` interface (`run(**kwargs) -> ToolResult`). Each tool returns a
`ToolResult(success, data, error, source)`, which lets callers handle failures
uniformly without knowing the tool's internals. Adding a new data source is just a
new `Tool` subclass registered on the shared registry — no agent changes required.

### Error Handling

- Every tool call is wrapped in a success/failure `ToolResult`; agents degrade
  gracefully (skip the failed data source, record the error, and continue).
- Invalid/missing financial data is caught at parse time and surfaces a fallback
  advisory rather than crashing.
- All errors are accumulated in `state["errors"]` and returned in the final output,
  alongside an `execution_log` for observability.

### Logging

A single root logger with a consistent `time | level | logger | message` format.
Each agent logs under its own `agent.<name>` namespace. The workflow additionally
records structured `execution_log` entries (which agent ran, what action it took, its
status) that are emitted in the final JSON so every decision is traceable.

---

## 2. Agent Interactions & Flow

The system is a linear, deterministic pipeline orchestrated by LangGraph:

```
START
  │
  ▼
[orchestrate] ── routes, determines client_id, records plan
  │
  ▼
[fetch_data]  ── loads JSON input, calls CRM + market tools (graceful on failure)
  │
  ▼
[analyze]     ── computes income/expenses/savings, runs anomaly detection
  │
  ▼
[generate_advisory] ── builds structured AdvisoryOutput from analysis
  │
  ▼
 END
```

**Orchestrator Agent** is the central coordinator: it validates the request, resolves
the `client_id`, and records the execution plan. In this linear workflow the graph
itself routes state; the orchestrator's routing responsibility is expressed through
the plan + error validation (it short-circuits the rest of the flow when the request
is invalid).

**Data Fetcher Agent** ingests client financial data (from an inline JSON payload or a
file path) and enriches it with CRM context and market indicators via the tool
registry. If a tool fails, it logs the error and continues with what it has.

**Analyzer Agent** performs the financial analysis:
- total income, expenses, and net savings
- top spending categories
- anomaly detection (see below)

**Advisor Agent** converts the analysis into a structured `AdvisoryOutput` with a
summary, insights, anomalies, and recommendations, and produces a fallback advisory if
no analysis is available.

### Anomaly Detection

1. **Large outlier transactions** — robust z-score using median absolute deviation
   (MAD), which is resilient to skewed/outlier-heavy data (unlike mean + stddev).
2. **Duplicate transactions** — same description + amount occurring within a short
   window (2 days), distinguishing true duplicates from recurring monthly bills.
3. **Negative account balances** — high-severity risk signal.

---

## 3. Key Decisions & Trade-offs

| Decision | Rationale | Trade-off |
|---|---|---|
| LangGraph `StateGraph` for orchestration | Declarative, testable flow; shared state typed via `TypedDict`; easy to later add branching/checkpoints | Slightly heavier dependency than a hand-rolled loop |
| `Tool` ABC + `ToolRegistry` | Enforces interface, centralizes tool discovery, keeps agents decoupled from implementations | A bit of indirection vs. direct function calls |
| Pydantic models for I/O boundaries | Early, clear validation of input and structured outputs | Runtime validation overhead (negligible here) |
| MAD-based outlier detection | Robust to the skewed distributions typical of transaction data | Slightly more complex than plain z-score |
| Mock tools with configurable `fail_rate`/`latency` | Deterministic tests of the error paths without a real network | Not production API clients |
| Errors collected in state rather than raised | Keeps the pipeline resilient and observability-friendly | Must be careful not to silently swallow bugs (hence `execution_log`) |

## 4. Assumptions

- Transaction amounts are **signed**: positive = inflow, negative = outflow.
- Dates are ISO `YYYY-MM-DD` strings.
- "Large" transactions are judged relative to the client's own transaction history
  (a fixed absolute threshold would misclassify across income levels).
- The amount-based outlier detector does **not** yet model recurring fixed expenses
  (e.g. monthly rent can appear "large" relative to the median transaction). This is a
  known limitation and an obvious next improvement (frequency/periodicity modeling).
- CRM and market data are mocked; the interfaces mirror what real clients would expose.

## 5. Instructions to Run

### Prerequisites

- Python 3.10+
- Git (for cloning)

### Setup

```bash
git clone <repo-url> wealth-advisor
cd wealth-advisor

# Create and activate a virtual environment (recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### Run

```bash
python -m wealth_advisor.main --client-data data/sample_client.json
```

Options:

```bash
python -m wealth_advisor.main --client-data data/sample_client.json --log-level DEBUG
```

### Run tests

```bash
python -m unittest discover -s tests -v
```

### Sample input

`data/sample_client.json` (abridged):

```json
{
  "client": { "client_id": "C001", "name": "Alice Johnson", "risk_profile": "conservative" },
  "accounts": [
    { "id": "A001", "type": "checking", "balance": 4250.0 },
    { "id": "A002", "type": "savings", "balance": 18000.0 },
    { "id": "A003", "type": "investment", "balance": -120.0 }
  ],
  "transactions": [
    { "id": "T001", "date": "2024-01-05", "description": "Salary", "category": "income", "amount": 5000.0, "account_id": "A001" },
    { "id": "T008", "date": "2024-01-25", "description": "Electronics", "category": "shopping", "amount": -12000.0, "account_id": "A001" }
  ]
}
```

### Sample output

```json
{
  "advisory": {
    "client_id": "C001",
    "summary": "Net savings of $-7,935.00 (income $10,000.00, expenses $17,935.00). 5 anomaly(ies) detected.",
    "insights": [
      "Top spending category is 'shopping' at $12,000.00.",
      "Client is spending more than they earn."
    ],
    "anomalies": [
      {
        "category": "large_outlier_transaction",
        "severity": "high",
        "description": "Unusually large outflow of $12,000.00 for 'Electronics'"
      },
      { "category": "duplicate_transaction", "severity": "medium", "description": "Possible duplicate transaction: 'Groceries' for $320.00" },
      { "category": "negative_balance", "severity": "high", "description": "Account 'A003' has a negative balance of $-120.00" }
    ],
    "recommendations": [
      "Consider a budget review to reduce expenses.",
      "Address negative account balances immediately.",
      "Review unusually large transactions with the client.",
      "Verify possible duplicate charges and request refunds if needed."
    ]
  },
  "errors": [],
  "execution_log": [
    { "agent": "orchestrator", "action": "route", "client_id": "C001", "plan": ["fetch_data", "analyze", "generate_advisory"] },
    { "agent": "data_fetcher", "action": "load_client_data", "status": "ok" },
    { "agent": "data_fetcher", "action": "fetch_crm", "status": "ok" },
    { "agent": "analyzer", "action": "analyze", "anomalies": 5 },
    { "agent": "advisor", "action": "generate_advisory", "status": "ok" }
  ]
}
```
