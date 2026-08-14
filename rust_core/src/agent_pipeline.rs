//! Agent Pipeline: Ajan düğümleri ve analiz sonuçları
//! Veri akışını ve ajan işleme boru hatlarını tanımlar.

use serde::{Deserialize, Serialize};

/// Analiz sonucu
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisResult {
    pub task_id: String,
    pub status: String,
    pub findings: Vec<String>,
    pub confidence: f32,
    pub payload: Option<String>,
}

/// Ajan düğüm durumu
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum HaltReason {
    Completed,
    Error(String),
    Timeout,
    ManualStop,
    LlmParseError(String),
    NetworkTimeout,
    UncertaintyHalt(String),
}

/// AgentNode: Bir ajan işleme düğümü
#[derive(Debug, Clone)]
pub struct AgentNode {
    pub node_id: String,
    pub node_type: String,
    pub is_active: bool,
}

impl AgentNode {
    pub fn new(node_type: &str) -> Self {
        Self {
            node_id: uuid::Uuid::new_v4().to_string(),
            node_type: node_type.to_string(),
            is_active: true,
        }
    }

    pub fn process(&self, input: &str) -> Result<AnalysisResult, &'static str> {
        if !self.is_active {
            return Err("Node is not active");
        }
        Ok(AnalysisResult {
            task_id: self.node_id.clone(),
            status: "completed".to_string(),
            findings: vec![format!("Processed: {}", input)],
            confidence: 0.95,
            payload: None,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_agent_node_creation() {
        let node = AgentNode::new("verifier");
        assert_eq!(node.node_type, "verifier");
        assert!(node.is_active);
    }

    #[test]
    fn test_agent_node_process() {
        let node = AgentNode::new("calculator");
        let result = node.process("test input");
        assert!(result.is_ok());
        let analysis = result.unwrap();
        assert_eq!(analysis.status, "completed");
    }
}
