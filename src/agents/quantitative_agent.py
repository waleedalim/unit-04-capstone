"""Quantitative NL-to-SQL agent: translates questions into SQL against the sales/customers DB."""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src import config
from src.db.init_db import init_db
from src.llm_client import FallbackLLMClient, LLMClient, get_llm_client

SCHEMA_DESCRIPTION = """\
Table sales(id INTEGER, sale_date TEXT 'YYYY-MM-DD', region TEXT, revenue REAL, quarter TEXT)
Table customers(id INTEGER, region TEXT, signup_date TEXT, churn_date TEXT NULL)
"""

BLOCKED_KEYWORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|attach|pragma|create)\b", re.IGNORECASE
)


@dataclass
class QuantitativeAnswer:
    sql: str
    columns: List[str] = field(default_factory=list)
    rows: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""


class SQLGenerationError(ValueError):
    pass


class QuantitativeAgent:
    """Translates natural language into SQL, executes it, and summarizes the result."""

    def __init__(self, db_path: Path = config.DB_PATH, llm_client: Optional[LLMClient] = None):
        if not db_path.exists():
            init_db(db_path)
        self.db_path = db_path
        self.llm = llm_client or get_llm_client()

    # -- NL -> SQL -----------------------------------------------------
    def _fallback_sql(self, query: str) -> Optional[str]:
        q = query.lower()

        if "churn" in q:
            return (
                "SELECT ROUND(100.0 * SUM(CASE WHEN churn_date IS NOT NULL THEN 1 ELSE 0 END) "
                "/ COUNT(*), 2) AS churn_rate_pct FROM customers;"
            )

        if "monthly" in q and "revenue" in q:
            return (
                "SELECT strftime('%m', sale_date) AS month, ROUND(SUM(revenue), 2) AS total_revenue "
                "FROM sales GROUP BY month ORDER BY month;"
            )

        quarter_match = re.search(r"\bq[1-4]\b", q)
        if quarter_match and "region" in q:
            quarter = quarter_match.group(0).upper()
            return (
                f"SELECT region, ROUND(SUM(revenue), 2) AS total_revenue FROM sales "
                f"WHERE quarter = '{quarter}' GROUP BY region ORDER BY total_revenue DESC;"
            )

        if "region" in q and ("compare" in q or "performance" in q):
            return (
                "SELECT region, ROUND(SUM(revenue), 2) AS total_revenue FROM sales "
                "GROUP BY region ORDER BY total_revenue DESC;"
            )

        if "revenue" in q and "total" in q:
            return "SELECT ROUND(SUM(revenue), 2) AS total_revenue FROM sales;"

        return None

    def translate_to_sql(self, query: str) -> str:
        if not isinstance(self.llm, FallbackLLMClient):
            prompt = (
                "Translate the question into a single SQLite SELECT statement using this schema:\n"
                f"{SCHEMA_DESCRIPTION}\n"
                f"Question: {query}\n"
                "Respond with ONLY the SQL statement, no explanation, no markdown fences."
            )
            sql = self.llm.complete(prompt).strip().strip("`").strip()
            if sql.lower().startswith("sql"):
                sql = sql[3:].strip()
            return sql

        sql = self._fallback_sql(query)
        if sql is None:
            raise SQLGenerationError(
                "Could not translate this question to SQL without an LLM configured. "
                "Set OPENAI_API_KEY, or rephrase using terms like 'monthly revenue', "
                "'churn rate', or 'compare regions'."
            )
        return sql

    # -- execution -----------------------------------------------------
    def execute(self, sql: str) -> pd.DataFrame:
        if not sql.strip().lower().startswith("select"):
            raise SQLGenerationError("Only SELECT statements are allowed.")
        if BLOCKED_KEYWORDS.search(sql):
            raise SQLGenerationError("Generated SQL contains a disallowed keyword.")

        conn = sqlite3.connect(self.db_path)
        try:
            return pd.read_sql_query(sql, conn)
        finally:
            conn.close()

    # -- answering -------------------------------------------------------
    def answer(self, query: str) -> QuantitativeAnswer:
        sql = self.translate_to_sql(query)
        df = self.execute(sql)

        if not isinstance(self.llm, FallbackLLMClient):
            summary = self.llm.complete(
                f"Question: {query}\nSQL result (as records): {df.to_dict(orient='records')}\n"
                "Write a short (1-3 sentence) plain-English insight based on this data."
            )
        else:
            summary = f"Query returned {len(df)} row(s). See table for details."

        return QuantitativeAnswer(
            sql=sql,
            columns=list(df.columns),
            rows=df.to_dict(orient="records"),
            summary=summary,
        )
