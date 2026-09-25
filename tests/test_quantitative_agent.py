import pytest

from src.agents.quantitative_agent import SQLGenerationError


def test_churn_rate_query(quant_agent):
    result = quant_agent.answer("What's our customer churn rate?")
    assert "churn" in result.sql.lower()
    assert len(result.rows) == 1
    assert "churn_rate_pct" in result.columns


def test_monthly_revenue_trend(quant_agent):
    result = quant_agent.answer("Show me monthly revenue trends")
    assert "group by" in result.sql.lower()
    assert len(result.rows) == 12  # one row per month


def test_compare_regions_q4(quant_agent):
    result = quant_agent.answer("Compare Q4 performance across regions")
    assert "q4" in result.sql.lower()
    regions = {row["region"] for row in result.rows}
    assert regions == {"North", "South", "East", "West"}


def test_unrecognized_query_without_llm_raises(quant_agent):
    with pytest.raises(SQLGenerationError):
        quant_agent.answer("What color is the sky today")


def test_execute_blocks_non_select():
    from src.agents.quantitative_agent import QuantitativeAgent
    from src.llm_client import FallbackLLMClient
    import tempfile
    from pathlib import Path
    from src.db.init_db import init_db

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "t.db"
        init_db(db_path)
        agent = QuantitativeAgent(db_path=db_path, llm_client=FallbackLLMClient())
        with pytest.raises(SQLGenerationError):
            agent.execute("DELETE FROM sales")
