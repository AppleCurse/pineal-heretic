import asyncio
from agent_core.task_executor import PinealExecutor
from tests.integration.test_p2_release_gate import mock_query_json
from unittest.mock import AsyncMock, patch

task_input = {
    'user_profile': {
        'private_rituals': ['çay', 'kitap', 'neset_ertas'],
        'late_night_playlist': ['neşet ertaş - gönül dağı'],
        'secret_envies': ['derin bağlantılar', 'anlaşılmak'],
        'authenticity_score': 0.85
    },
    'target_profile': {
        'images': [],
        'bio': "Sadece pozitif enerji ✨",
        'posts': ["Cuma akşamı evdeyim yorgunum 😴"]
    }
}

async def run():
    executor = PinealExecutor()
    from agent_core.agents.pattern_interrupt import PatternInterrupt
    executor.agents['pattern_interrupt'] = PatternInterrupt()
    def my_log(level, msg):
        print(f'[{level}] {msg}')
    executor._log = my_log
    executor.search_engine.tavily_key = "mock_key"
    from agent_core.services.search_engine import SearchResult
    executor.search_engine.search = AsyncMock(return_value=[
        SearchResult(query="dummy", content="Sadece pozitif enerji", source_url="http://mock.com")
    ])
    with patch('agent_core.services.llm_gateway.LLMGateway.query_json', new=AsyncMock(side_effect=mock_query_json)):
        res = await executor.execute_task(task_input, 'p2_release_gate')
        for step in res.evidence_chain:
            print(f"[{step['agent']}] Result: {step.get('result', {})}")
        print(f"Final Status: {res.status}")

asyncio.run(run())

