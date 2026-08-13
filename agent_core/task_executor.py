import asyncio, os, tempfile, traceback
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

try:
    from agent_core.services.cognitive_router import CognitiveRouter, RoutePlan
    from agent_core.services.canonical_memory import CanonicalMemory
    from agent_core.services.uncertainty_engine import UncertaintyEngine
    from agent_core.services.llm_gateway import LLMGateway
    from agent_core.agents.human_behavior import HumanBehaviorAnalyzer
    from agent_core.agents.mirror_truth import MirrorOfTruth
    from agent_core.agents.resonance_calculator import ResonanceCalculator
    from agent_core.agents.pattern_interrupt import PatternInterrupt
    from agent_core.services.memory_injector import MemoryInjector
except Exception:
    from services.cognitive_router import CognitiveRouter, RoutePlan
    from services.canonical_memory import CanonicalMemory
    from services.uncertainty_engine import UncertaintyEngine
    from services.llm_gateway import LLMGateway
    from agents.human_behavior import HumanBehaviorAnalyzer
    from agents.mirror_truth import MirrorOfTruth
    from agents.resonance_calculator import ResonanceCalculator
    from agents.pattern_interrupt import PatternInterrupt
    from services.memory_injector import MemoryInjector

class InsufficientEvidenceError(RuntimeError):
    pass

class VerifiedNote(BaseModel):
    note: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    current_agent: Optional[str] = None
    evidence_chain: List[Dict] = []
    created_at: datetime = None
    completed_at: Optional[datetime] = None

class PinealExecutor:
    def __init__(self, log_callback=None):
        self._log = log_callback or (lambda level, msg: None)
        self.router = CognitiveRouter()
        self.memory = CanonicalMemory()
        self.injector = MemoryInjector()
        self.uncertainty = UncertaintyEngine()
        self.llm_gateway = LLMGateway()
        self.agents = {
            "human_behavior": HumanBehaviorAnalyzer(),
            "mirror_truth": MirrorOfTruth(),
            "resonance_calc": ResonanceCalculator(),
            "pattern_interrupt": PatternInterrupt(),
        }

    async def _download_images(self, urls: List[str]) -> List[str]:
        paths = []
        for u in urls[:2]:
            try:
                import httpx
                async with httpx.AsyncClient() as c:
                    r = await c.get(u, timeout=15)
                    r.raise_for_status()
                    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
                    tmp.write(r.content)
                    tmp.close()
                    paths.append(tmp.name)
            except Exception as e:
                self._log("WARNING", "Gorsel indirilemedi: " + str(e)[:60])
        return paths

    @staticmethod
    def _user_vector(mirror) -> Dict[str, float]:
        f = mirror.user_core_frequency
        if "derin" in f:
            return {"depth": 0.9, "energy": 0.3, "authenticity": 0.9}
        if "arayici" in f:
            return {"depth": 0.6, "energy": 0.5, "authenticity": 0.6}
        return {"depth": 0.2, "energy": 0.8, "authenticity": 0.3}

    @staticmethod
    def _target_vector(reading) -> Dict[str, float]:
        sig = reading.micro_signals
        tension = sum(1 for s in sig if s.signal_type == "tension")
        void = sum(1 for s in sig if s.signal_type == "void")
        auth = sum(1 for s in sig if s.signal_type == "authentic")
        return {
            "depth": min(0.3 + 0.2 * (void + tension), 1.0),
            "energy": min(0.2 + 0.15 * len(sig), 1.0),
            "authenticity": min(0.3 + 0.2 * auth, 1.0),
        }

    async def _deep_research(self, input_data, suspicious, agent_name):
        prompt = (
            "Onceki analiz supheli bulundu. Kanit: " + suspicious.json() +
            "\nKurallar: 1) Emin degilsen 'bilmiyorum' de 2) Tahmin uretme 3) Sadece veride olanlari analiz et. Yeniden analiz et."
        )
        verified = await self.llm_gateway.query(prompt, temperature=0.1)
        return VerifiedNote(note=verified)

    async def execute_task(self, input_data: Dict[str, Any], task_id: str) -> TaskStatus:
        status = TaskStatus(task_id=task_id, status="pending", created_at=datetime.utcnow())
        status.status = "processing"

        # Kutsal Kuralları (Hafıza) Enjekte Et
        sacred_rules = self.injector.fetch_active_rules()
        input_data["sacred_rules"] = sacred_rules

        imgs = input_data.get("target_profile", {}).get("images", [])
        if imgs and isinstance(imgs[0], str) and imgs[0].startswith("http"):
            input_data["target_profile"]["images"] = await self._download_images(imgs)

        route: RoutePlan = await self.router.analyze(input_data)
        self._log("INFO", "[" + task_id + "] ROUTE: " + " -> ".join(route.agents))

        deferred = []
        try:
            for agent_name in route.agents:
                if agent_name == "pattern_interrupt":
                    deferred.append(agent_name)
                    continue
                if agent_name not in self.agents:
                    raise KeyError("Bilinmeyen yetenek: " + agent_name)
                status.current_agent = agent_name
                self._log("WARNING", "[" + task_id + "] AGENT " + agent_name + ": calisiyor")
                result = await self.agents[agent_name].execute(input_data, self.memory, self.llm_gateway)
                if not isinstance(result, BaseModel):
                    raise TypeError(agent_name + " gecersiz cikti: " + str(type(result)))

                check = self.uncertainty.evaluate(result, agent_name)
                
                # Dinamik Karar Ağacı: Eğer güven çok düşükse direkt kes (Router devreye girer)
                if check.confidence < 0.6:
                    halt_reason = f"Düşük güven ({check.confidence}). Router zinciri kesti."
                    self._log("ERROR", f"[{task_id}] COGNITIVE ROUTER: {halt_reason}")
                    raise InsufficientEvidenceError(halt_reason)
                    
                if check.is_suspicious:
                    self._log("ERROR", "[" + task_id + "] UNCERTAINTY: " + check.reason)
                    try:
                        result = await self._deep_research(input_data, result, agent_name)
                    except Exception as e:
                        raise InsufficientEvidenceError("Supheli kanit dogrulanamadi: " + str(e)[:80])

                if agent_name == "mirror_truth":
                    input_data["user_mirror"] = result.dict() if hasattr(result, 'dict') else result.model_dump()
                    # Vector hesaplamaları için mock
                    input_data["user_authentic_vector"] = {"depth": 0.9, "energy": 0.3}
                if agent_name == "human_behavior":
                    input_data["target_analysis"] = result.dict() if hasattr(result, 'dict') else result.model_dump()
                    input_data["target_authentic_vector"] = {"depth": 0.8, "energy": 0.4}

                status.evidence_chain.append({"agent": agent_name, "result": result.dict() if hasattr(result, 'dict') else result.model_dump(), "timestamp": datetime.utcnow().isoformat()})

                if agent_name == "resonance_calc" and result.compatibility_score < 0.70:
                    self._log("ERROR", "[" + task_id + "] FREKANS UYUSMAZLIGI: " + str(round(result.compatibility_score, 2)))
                    status.status = "halted_frequency"
                    await self.memory.merge_evidence(task_id, status.evidence_chain)
                    return status

            for agent_name in deferred:
                status.current_agent = agent_name
                self._log("WARNING", "[" + task_id + "] AGENT " + agent_name + ": calisiyor")
                result = await self.agents[agent_name].execute(input_data, self.memory, self.llm_gateway)
                status.evidence_chain.append({"agent": agent_name, "result": result.dict() if hasattr(result, 'dict') else result.model_dump(), "timestamp": datetime.utcnow().isoformat()})
                self._log("INFO", "[" + task_id + "] HOOK: mesaj dovuldu")

            status.status = "completed"
            status.completed_at = datetime.utcnow()
            await self.memory.merge_evidence(task_id, status.evidence_chain)
            self._log("INFO", "[" + task_id + "] TAMAMLANDI. Kanit adimi: " + str(len(status.evidence_chain)))

        except InsufficientEvidenceError as e:
            self._log("ERROR", "[" + task_id + "] KANIT KILIDI: " + str(e))
            status.status = "halted_evidence"
            await self.memory.merge_evidence(task_id, status.evidence_chain)
        return status

executor = PinealExecutor()
