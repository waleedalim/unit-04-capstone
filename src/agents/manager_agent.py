"""Manager agent: classifies queries and routes them to the right specialist agent(s)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.agents.qualitative_agent import QualitativeAgent, QualitativeAnswer
from src.agents.quantitative_agent import QuantitativeAgent, QuantitativeAnswer, SQLGenerationError

QUALITATIVE_KEYWORDS = [
    "policy", "process", "explain", "how do we", "what is our", "handle",
    "guideline", "procedure", "security", "review process", "complaint",
]
QUANTITATIVE_KEYWORDS = [
    "revenue", "trend", "rate", "compare", "average", "total", "how many",
    "count", "churn", "sales", "performance", "percentage", "number of",
    "q1", "q2", "q3", "q4",
]

QueryType = str  # "qualitative" | "quantitative" | "complex" | "unclear"


@dataclass
class ManagerResponse:
    query: str
    query_type: QueryType
    answer: str
    qualitative: Optional[QualitativeAnswer] = None
    quantitative: Optional[QuantitativeAnswer] = None


class ManagerAgent:
    """Routes each query to the qualitative agent, quantitative agent, or both."""

    def __init__(
        self,
        qualitative_agent: Optional[QualitativeAgent] = None,
        quantitative_agent: Optional[QuantitativeAgent] = None,
    ):
        self.qualitative_agent = qualitative_agent or QualitativeAgent()
        self.quantitative_agent = quantitative_agent or QuantitativeAgent()

    def classify_query(self, query: str) -> QueryType:
        q = query.lower()
        qual_hit = any(kw in q for kw in QUALITATIVE_KEYWORDS)
        quant_hit = any(kw in q for kw in QUANTITATIVE_KEYWORDS)

        if qual_hit and quant_hit:
            return "complex"
        if quant_hit:
            return "quantitative"
        if qual_hit:
            return "qualitative"
        return "unclear"

    def handle_query(self, query: str) -> ManagerResponse:
        query_type = self.classify_query(query)

        if query_type == "unclear":
            return ManagerResponse(
                query=query,
                query_type=query_type,
                answer=(
                    "I'm not sure whether this is a documentation question or a data "
                    "question. Could you clarify -- are you asking about a policy/process, "
                    "or about numbers/metrics from our data?"
                ),
            )

        if query_type == "qualitative":
            qual = self.qualitative_agent.answer(query)
            return ManagerResponse(query=query, query_type=query_type, answer=qual.answer, qualitative=qual)

        if query_type == "quantitative":
            try:
                quant = self.quantitative_agent.answer(query)
                answer_text = quant.summary
            except SQLGenerationError as exc:
                quant = None
                answer_text = str(exc)
            return ManagerResponse(query=query, query_type=query_type, answer=answer_text, quantitative=quant)

        # complex: needs both agents, merged into one labeled answer
        qual = self.qualitative_agent.answer(query)
        try:
            quant = self.quantitative_agent.answer(query)
            quant_text = quant.summary
        except SQLGenerationError as exc:
            quant = None
            quant_text = str(exc)

        merged = (
            "This question has both a documentation and a data component.\n\n"
            f"[Qualitative Agent -- documentation]\n{qual.answer}\n\n"
            f"[Quantitative Agent -- data]\n{quant_text}"
        )
        return ManagerResponse(
            query=query, query_type=query_type, answer=merged, qualitative=qual, quantitative=quant
        )
