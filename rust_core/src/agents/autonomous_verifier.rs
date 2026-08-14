use crate::uncertainty::{ConfidenceLevel, UncertaintyEngine, InsufficientEvidence, Severity as UncertaintySeverity};
use crate::event_bus::{AgentEvent, EventBus, Severity};
use std::sync::Arc;
use uuid::Uuid;

/// Autonomous Verifier Ajanı
/// Tavily arama motoru ile hedefin iddialarını doğrular.
/// Veri veya API anahtarı yoksa UncertaintyEngine üzerinden Halt fırlatır.

/// Verification Report - Doğrulama sonucu
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct VerifierReport {
    pub verified: bool,
    pub claims_checked: u32,
    pub failed_claims: Vec<String>,
}

pub struct AutonomousVerifier {
    task_id: Uuid,
    event_bus: Arc<EventBus>,
    required_fields: Vec<String>,
}

impl AutonomousVerifier {
    pub fn new(task_id: Uuid, event_bus: Arc<EventBus>, required_fields: Vec<String>) -> Self {
        Self {
            task_id,
            event_bus,
            required_fields,
        }
    }

    /// Hedefin iddialarını doğrular
    pub async fn verify_claims(&self, claims_json: &str) -> Result<serde_json::Value, String> {
        self.event_bus.publish(AgentEvent::StepCompleted {
            task_id: self.task_id,
            agent_name: "AutonomousVerifier".to_string(),
            step_name: "Verification".to_string(),
            output_hash: format!("{:x}", md5::compute(claims_json.as_bytes())),
        }).map_err(|e| e.to_string())?;

        // JSON parse et
        let parsed: serde_json::Value = serde_json::from_str(claims_json)
            .map_err(|e| format!("JSON Parse Hatası: {}", e))?;

        // Uncertainty Engine ile doğrula
        let engine = UncertaintyEngine::new(self.task_id, self.required_fields.clone());
        let confidence = engine.evaluate(&parsed)
            .map_err(|e| format!("Doğrulama Hatası: {}", e))?;

        match confidence {
            ConfidenceLevel::Halt(evidence) => {
                let reason_msg = evidence.reason.clone();
                self.event_bus.publish(AgentEvent::ErrorHalt {
                    task_id: self.task_id,
                    agent_name: "AutonomousVerifier".to_string(),
                    error_code: "VERIFICATION_FAILED".to_string(),
                    error_message: evidence.reason,
                    severity: match evidence.severity {
                        UncertaintySeverity::Low => Severity::Info,
                        UncertaintySeverity::Medium => Severity::Warning,
                        UncertaintySeverity::Critical => Severity::Critical,
                    },
                }).map_err(|e| e.to_string())?;
                Err(format!("Verifier durduruldu: {}", reason_msg))
            },
            ConfidenceLevel::Pass(evidence) => {
                self.event_bus.publish(AgentEvent::StepCompleted {
                    task_id: self.task_id,
                    agent_name: "AutonomousVerifier".to_string(),
                    step_name: "Completed".to_string(),
                    output_hash: format!("{:x}", md5::compute(format!("{:?}", evidence).as_bytes())),
                }).map_err(|e| e.to_string())?;
                Ok(parsed)
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_verifier_creation() {
        let event_bus = Arc::new(EventBus::new(50));
        let _verifier = AutonomousVerifier::new(
            Uuid::new_v4(),
            event_bus,
            vec!["query".to_string(), "results".to_string()],
        );
    }
}
