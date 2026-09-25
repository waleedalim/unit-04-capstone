import pytest

from src import config
from src.agents.manager_agent import ManagerAgent
from src.agents.qualitative_agent import QualitativeAgent
from src.agents.quantitative_agent import QuantitativeAgent
from src.db.init_db import init_db
from src.llm_client import FallbackLLMClient


@pytest.fixture
def quant_agent(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    return QuantitativeAgent(db_path=db_path, llm_client=FallbackLLMClient())


@pytest.fixture
def qual_agent(tmp_path):
    return QualitativeAgent(
        docs_dir=config.DOCS_DIR,
        persist_dir=tmp_path / "vectorstore",
        llm_client=FallbackLLMClient(),
    )


@pytest.fixture
def manager(qual_agent, quant_agent):
    return ManagerAgent(qualitative_agent=qual_agent, quantitative_agent=quant_agent)
