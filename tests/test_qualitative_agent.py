def test_retrieves_relevant_citation_for_security_policy(qual_agent):
    result = qual_agent.answer("What is our company's security policy?")
    assert result.found_relevant_docs
    assert any(c.source == "security_policy.md" for c in result.citations)
    assert all(c.similarity >= qual_agent.relevance_threshold for c in result.citations)


def test_retrieves_relevant_citation_for_code_review(qual_agent):
    result = qual_agent.answer("Explain the code review process")
    assert result.found_relevant_docs
    assert any(c.source == "code_review_process.md" for c in result.citations)


def test_off_topic_question_scores_lower_than_on_topic(qual_agent):
    on_topic = qual_agent.retrieve("What is our company's security policy?", k=1)
    off_topic = qual_agent.retrieve(
        "What is the airspeed velocity of an unladen swallow?", k=1
    )
    on_topic_score = on_topic[0].similarity if on_topic else 0
    off_topic_score = off_topic[0].similarity if off_topic else 0
    assert on_topic_score > off_topic_score
