use async_trait::async_trait;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisResult {
    pub confidence: f32,
    pub payload: String,
}

#[derive(Debug, Clone)]
pub enum HaltReason {
    InsufficientEvidence(String),
    LlmParseError(String),
    NetworkTimeout,
    UncertaintyHalt(String), // eklendi
}

/// A Strict Type-Safe pipeline trait that ensures we NEVER default to fake data.
/// Instead of returning a manipulated Dict, we return a Result.
#[async_trait]
pub trait AgentNode {
    fn name(&self) -> &'static str;
    
    /// Executes the agent logic. MUST return an explicit Result.
    async fn execute(&self, input: &str) -> Result<AnalysisResult, HaltReason>;
}
