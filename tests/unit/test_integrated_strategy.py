import pytest
from unittest.mock import MagicMock, patch
import asyncio
from agent_core.aspasia.integrated_strategy import (
    IntegratedStrategyEngine,
    SuperStrategy,
    generate_strategy_for_rust
)
from agent_core.aspasia.psychological_profiler import PsychologicalProfile, AttachmentStyle
from agent_core.aspasia.dopamine_engine import DopamineProfile, RewardSchedule
from agent_core.services.llm_gateway import LLMGateway

@pytest.fixture
def engine():
    return IntegratedStrategyEngine()

@pytest.fixture
def mock_profiles():
    psych = PsychologicalProfile(
        attachment=AttachmentStyle.ANXIOUS,
        core_wound='abandonment',
        fear='Terk edilme',
        emotional_need='Güvenlik',
        dark_triad={'machiavellianism': 0.1, 'narcissism': 0.8, 'psychopathy': 0.1},
        exploitability=0.9,
        attention_seeking=0.8,
        validation_frequency=0.2
    )
    
    dop = DopamineProfile(
        validation_need=0.9,
        novelty_seeking=0.8,
        uncertainty_tolerance=0.2,
        chase_sensitivity=0.9,
        loss_chasing=True,
        near_miss_sensitivity=0.8,
        optimal_reward=RewardSchedule.VARIABLE_RATIO,
        optimal_interval=60
    )
    return psych, dop

def test_analyze_and_synthesize_full_flow(engine):
    target_data = {
        'posts': ['Lütfen beğeni atın', 'Yorum bekliyorum', 'terk edildim', 'yalnızım']
    }
    
    # Internal logic is not mocked! We run the real engines
    strategy = engine.analyze_and_synthesize(target_data)
    
    assert isinstance(strategy, SuperStrategy)
    assert strategy.psychological is not None
    assert strategy.dopamine is not None
    assert len(strategy.message_sequence) == 10
    
    # Check phases
    phases = [msg['phase'] for msg in strategy.message_sequence]
    assert 'wound_hook' in phases
    assert 'variable_reward_2' in phases
    assert 'open_loop' in phases
    assert 'maintenance_6' in phases

def test_calculate_addiction_risk(engine, mock_profiles):
    psych, dop = mock_profiles
    risk = engine._calculate_addiction_risk(psych, dop)
    # Exploitability (0.9*0.3=0.27) + Attention (0.8*0.2=0.16) + Validation (0.8*0.1=0.08) = 0.51
    # Chase (0.9*0.2=0.18) + Near Miss (0.8*0.15=0.12) + Uncertainty (0.8*0.05=0.04) = 0.34
    # Total ~ 0.85 -> addictive
    assert risk > 0.8
    assert engine._assess_risk(risk) == "addictive"
    assert "Etik sınırları aşıyor" in engine._generate_warning(risk)

def test_craft_wound_hook_fallback(engine, mock_profiles):
    psych, dop = mock_profiles
    # Without LLM, it uses static fallback dictionaries
    hook = engine._craft_wound_hook(psych, dop, llm_gateway=None)
    assert len(hook) > 0
    assert "Bir daha denemeliyim" in hook  # Chase sensitivity is 0.9 > 0.6

def test_craft_wound_hook_llm_success(engine, mock_profiles):
    psych, dop = mock_profiles
    mock_llm = MagicMock(spec=LLMGateway)
    
    # We mock LLMGateway.query which is an async function.
    # However, in _craft_wound_hook it's wrapped in asyncio.get_event_loop().run_until_complete
    # We need to simulate the return of the coroutine
    async def mock_query(*args, **kwargs):
        return "Yalnızlığını anlıyorum."
        
    mock_llm.query = mock_query
    
    # We need to run it in a way that asyncio loop works, or since we are in a test env,
    # if it's already running, it might skip it. Let's see.
    # We will just patch the `run_until_complete` branch or simulate it.
    
    with patch('asyncio.get_event_loop') as mock_loop:
        mock_loop_instance = MagicMock()
        # Mock is_running to False so it uses run_until_complete
        mock_loop_instance.is_running.return_value = False
        mock_loop_instance.run_until_complete.return_value = "Yalnızlığını anlıyorum."
        mock_loop.return_value = mock_loop_instance
        
        hook = engine._craft_wound_hook(psych, dop, llm_gateway=mock_llm)
        
        assert "Yalnızlığını anlıyorum." in hook
        assert "Bir daha denemeliyim" in hook

def test_craft_wound_hook_llm_exception_fallback(engine, mock_profiles):
    psych, dop = mock_profiles
    mock_llm = MagicMock(spec=LLMGateway)
    
    with patch('asyncio.get_event_loop') as mock_loop:
        mock_loop_instance = MagicMock()
        mock_loop_instance.is_running.return_value = False
        mock_loop_instance.run_until_complete.side_effect = Exception("Network Error")
        mock_loop.return_value = mock_loop_instance
        
        # Exception should be caught and fallback used
        hook = engine._craft_wound_hook(psych, dop, llm_gateway=mock_llm)
        assert len(hook) > 0
        assert "Bir daha denemeliyim" in hook

def test_generate_strategy_for_rust():
    target_data = {'posts': ['harikayım']}
    result = generate_strategy_for_rust(target_data)
    
    assert 'psychological_profile' in result
    assert 'dopamine_profile' in result
    assert 'strategy' in result
    assert 'warning' in result
    assert isinstance(result['strategy']['sequence'], list)
    assert len(result['strategy']['sequence']) == 10
