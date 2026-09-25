from src.cli import format_response
from src.agents.manager_agent import ManagerResponse
from src.agents.quantitative_agent import QuantitativeAnswer
from src.agents.qualitative_agent import QualitativeAnswer, Citation


def test_format_response_includes_citations():
    response = ManagerResponse(
        query="What is our security policy?",
        query_type="qualitative",
        answer="We require MFA.",
        qualitative=QualitativeAnswer(
            answer="We require MFA.",
            citations=[Citation(source="security_policy.md", chunk_id="security_policy::0", similarity=0.8, text="...")],
        ),
    )
    output = format_response(response)
    assert "We require MFA." in output
    assert "security_policy.md" in output


def test_format_response_includes_sql_table():
    response = ManagerResponse(
        query="churn rate?",
        query_type="quantitative",
        answer="18% churn",
        quantitative=QuantitativeAnswer(
            sql="SELECT 1 AS churn_rate_pct;",
            columns=["churn_rate_pct"],
            rows=[{"churn_rate_pct": 18.0}],
            summary="18% churn",
        ),
    )
    output = format_response(response)
    assert "SELECT 1 AS churn_rate_pct" in output
    assert "18" in output


def test_cli_one_shot_query(manager, monkeypatch, capsys):
    from src import cli

    monkeypatch.setattr(cli, "ManagerAgent", lambda: manager)
    exit_code = cli.main(["-q", "What is our company's security policy?"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "QUALITATIVE" in captured.out
