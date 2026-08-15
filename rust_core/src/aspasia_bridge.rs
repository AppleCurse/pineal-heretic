use std::process::{Command, Stdio};
use serde::{Deserialize, Serialize};
use tauri::State;

#[derive(Serialize, Deserialize, Debug)]
pub struct IntegratedResult {
    pub psychological_profile: PsychProfile,
    pub dopamine_profile: DopamineProfile,
    pub strategy: StrategyResult,
    pub warning: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct PsychProfile {
    pub attachment: String,
    pub core_wound: String,
    pub exploitability: f64,
    pub dark_triad: DarkTriad,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct DopamineProfile {
    pub chase_sensitivity: f64,
    pub validation_need: f64,
    pub optimal_schedule: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct StrategyResult {
    pub sequence: Vec<MessageStep>,
    pub addiction_potential: f64,
    pub compliance_probability: f64,
    pub risk_level: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct MessageStep {
    pub phase: String,
    pub content: String,
    pub mechanism: String,
    pub delay: u64,
    pub dopamine_spike: f64,
    pub trust_building: bool,
    pub attachment_cue: Option<String>,
    pub trigger: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct DarkTriad {
    pub machiavellianism: f64,
    pub narcissism: f64,
    pub psychopathy: f64,
}

#[derive(Clone)]
pub struct AspasiaBridge;

impl AspasiaBridge {
    pub fn analyze_target(&self, target_data: serde_json::Value) -> Result<IntegratedResult, String> {
        // Python Aspasia motorunu çağır
        let python_script = format!(r#"
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), '..', '..', 'agent_core')))
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), '..', 'agent_core')))
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), 'agent_core')))

try:
    from aspasia.integrated_strategy import generate_strategy_for_rust
except ImportError as e:
    import json
    print(json.dumps({{"error": str(e)}}))
    sys.exit(1)
import json

data = json.loads('{}')
result = generate_strategy_for_rust(data)

print(json.dumps(result))
"#, target_data.to_string().replace("'", r"\'"));

        let python_path = std::env::var("PYTHONPATH").unwrap_or_default();
        let python_path = format!("{};agent_core", python_path);
        
        let output = Command::new("python")
            .env("PYTHONPATH", python_path)
            .env("PYTHONIOENCODING", "utf-8")
            .arg("-c")
            .arg(&python_script)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()
            .map_err(|e| format!("Python execution failed: {}", e))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!("Aspasia error: {}", stderr));
        }

        let stdout = String::from_utf8_lossy(&output.stdout);
        let profile: IntegratedResult = serde_json::from_str(&stdout)
            .map_err(|e| format!("JSON parse error: {}\nOutput: {}", e, stdout))?;

        Ok(profile)
    }
}

// Tauri Command
#[tauri::command]
pub async fn analyze_with_aspasia(
    target_data: serde_json::Value,
    state: State<'_, crate::tauri_bridge::CoreState>,
) -> Result<IntegratedResult, String> {
    let bridge = state.aspasia_bridge.clone();
    let data = target_data.clone();
    tokio::task::spawn_blocking(move || {
        bridge.analyze_target(data)
    })
    .await
    .map_err(|e| format!("Task join error: {}", e))?
}
