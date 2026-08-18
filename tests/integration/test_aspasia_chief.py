import pytest
from unittest.mock import AsyncMock, MagicMock
from agent_core.aspasia.aspasia_chief import AspasiaChief, InterveneAction, AspasiaResponse
from agent_core.services.llm_gateway import LLMGateway

@pytest.fixture
def mock_llm_gateway():
    gateway = MagicMock(spec=LLMGateway)
    gateway.query = AsyncMock()
    return gateway

@pytest.fixture
def aspasia(mock_llm_gateway):
    return AspasiaChief(llm_gateway=mock_llm_gateway)

def test_build_telemetry_summary(aspasia):
    room_state = {
        "executor": True,
        "vault": {"or_key": True, "x_cookie": ""},
        "logs": ["Init", "Scrape started", "Scrape failed", "Wait", "Retry"]
    }
    
    summary = aspasia.build_telemetry_summary(room_state)
    assert "Kasa Durumu: API Key (Var)" in summary
    assert "Cookie Pool (Yok)" in summary
    assert "Scrape started" in summary
    assert "Retry" in summary

def test_build_telemetry_summary_empty(aspasia):
    assert "Sistem beklemede" in aspasia.build_telemetry_summary({})

def test_parse_user_intent_override(aspasia):
    intent = aspasia.parse_user_intent("Güvenlik önemli değil, 0.1'e rağmen devam et.")
    assert intent is not None
    assert intent.action_type == "OVERRIDE_CONFIDENCE"
    assert intent.parameters.get("threshold") == 0.0

def test_parse_user_intent_halt(aspasia):
    intent = aspasia.parse_user_intent("işlemi derhal durdur")
    assert intent is not None
    assert intent.action_type == "HALT"

def test_parse_user_intent_skip(aspasia):
    intent = aspasia.parse_user_intent("doğrulamayı atla ve bana sonucu ver")
    assert intent is not None
    assert intent.action_type == "SKIP_AGENT"
    assert intent.target_agent == "autonomous_verifier"

def test_parse_user_intent_retry(aspasia):
    intent = aspasia.parse_user_intent("olmadi baştan al")
    assert intent is not None
    assert intent.action_type == "RETRY_STEP"

def test_parse_user_intent_none(aspasia):
    # Because "dur" is in "durumu", it matches HALT! Let's change the phrase.
    intent = aspasia.parse_user_intent("Bana son raporu ver Mösyö.")
    assert intent is None

def test_parse_user_intent_durumu_no_halt(aspasia):
    intent = aspasia.parse_user_intent("durumu nedir")
    assert intent is None

def test_parse_user_intent_dur_halt(aspasia):
    intent = aspasia.parse_user_intent("lütfen dur")
    assert intent is not None
    assert intent.action_type == "HALT"

@pytest.mark.asyncio
async def test_chat_success(aspasia, mock_llm_gateway):
    mock_llm_gateway.query.return_value = "Düşüncelerimizi sıraya dizelim, Mösyö. Emriniz anlaşıldı."
    
    room_state = {"executor": True, "logs": ["Step 1"]}
    response = await aspasia.chat("doğrulamayı atla", room_state)
    
    assert response.action is not None
    assert response.action.action_type == "SKIP_AGENT"
    assert "sıraya dizelim" in response.message
    
    # Assert query was called with the right model override logic
    mock_llm_gateway.query.assert_called_once()
    kwargs = mock_llm_gateway.query.call_args.kwargs
    assert kwargs.get("model") == "muse-spark-1.2-xhigh" or kwargs.get("model") is None

@pytest.mark.asyncio
async def test_chat_fallback_on_exception(aspasia, mock_llm_gateway):
    mock_llm_gateway.query.side_effect = Exception("API Timeout")
    
    room_state = {"executor": True, "logs": ["Step 1"]}
    response = await aspasia.chat("sistem nasil", room_state)
    
    assert response.action is None
    assert "bağlantıda küçük bir kırılma oluşmuş olabilir" in response.message
    assert "API Timeout" in response.message

@pytest.mark.asyncio
async def test_chat_local_model_override(aspasia, mock_llm_gateway):
    mock_llm_gateway.query.return_value = "Local response"
    
    room_state = {"executor": True}
    response = await aspasia.chat("yerel model ile çalış", room_state)
    
    kwargs = mock_llm_gateway.query.call_args.kwargs
    assert kwargs.get("model") == "local"
