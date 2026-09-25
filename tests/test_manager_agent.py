def test_classifies_qualitative_query(manager):
    assert manager.classify_query("Explain the code review process") == "qualitative"


def test_classifies_quantitative_query(manager):
    assert manager.classify_query("Show me monthly revenue trends") == "quantitative"


def test_classifies_complex_query(manager):
    query = "Compare Q4 performance across regions and explain our code review process"
    assert manager.classify_query(query) == "complex"


def test_classifies_unclear_query(manager):
    assert manager.classify_query("hello there") == "unclear"


def test_routes_qualitative_query_end_to_end(manager):
    response = manager.handle_query("What is our company's security policy?")
    assert response.query_type == "qualitative"
    assert response.qualitative is not None
    assert response.quantitative is None
    assert response.qualitative.citations


def test_routes_quantitative_query_end_to_end(manager):
    response = manager.handle_query("What's our customer churn rate?")
    assert response.query_type == "quantitative"
    assert response.quantitative is not None
    assert response.qualitative is None


def test_unclear_query_asks_for_clarification(manager):
    response = manager.handle_query("hello there")
    assert response.query_type == "unclear"
    assert "clarify" in response.answer.lower()


def test_complex_query_merges_both_agents(manager):
    query = "Compare Q4 performance across regions and explain our code review process"
    response = manager.handle_query(query)
    assert response.query_type == "complex"
    assert response.qualitative is not None
    assert response.quantitative is not None
    assert "[Qualitative Agent" in response.answer
    assert "[Quantitative Agent" in response.answer
