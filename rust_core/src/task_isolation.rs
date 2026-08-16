use uuid::Uuid;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use tokio::process::Command;
use serde_json::Value;
use crate::event_bus::{EventBus, AgentEvent, Severity};

#[derive(Debug, Clone)]
pub struct TaskContext {
    pub task_id: Uuid,
    pub state: HashMap<String, String>,
}

pub struct TaskManager {
    tasks: Arc<Mutex<HashMap<Uuid, TaskContext>>>,
    event_bus: Arc<EventBus>,
    python_path: String,
    scraper_path: String,
    executor_path: String,
}

impl TaskManager {
    pub fn new(event_bus: Arc<EventBus>) -> Self {
        // Proje kökünü bul (cargo manifest'den)
        let manifest_dir = std::env::var("CARGO_MANIFEST_DIR")
            .unwrap_or_else(|_| "/workspace/rust_core".to_string());
        let project_root = std::path::Path::new(&manifest_dir)
            .parent()
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_else(|| "/workspace".to_string());

        Self {
            tasks: Arc::new(Mutex::new(HashMap::new())),
            event_bus,
            python_path: "python3".to_string(),
            scraper_path: format!("{}/scraper.py", project_root),
            executor_path: format!("{}/agent_core/task_executor.py", project_root),
        }
    }

    pub fn create_task(&self) -> Uuid {
        let task_id = Uuid::new_v4();
        let ctx = TaskContext {
            task_id,
            state: HashMap::new(),
        };
        self.tasks.lock().unwrap().insert(task_id, ctx);
        task_id
    }

    pub fn get_task(&self, task_id: &Uuid) -> Option<TaskContext> {
        self.tasks.lock().unwrap().get(task_id).cloned()
    }

    /// Tam ajan hattı: Scraper + rust_bridge_agent (PinealExecutor zinciri)
    /// target_url, user_rituals, user_playlist, user_envies parametrelerini alıp
    /// agent_core/agents/rust_bridge_agent.py üzerinden işler
    pub async fn execute_isolated_task(
        &self,
        target_url: String,
        user_rituals: Vec<String>,
        user_playlist: Vec<String>,
        user_envies: Vec<String>,
    ) -> Result<String, String> {
        let task_id = self.create_task();

        let _ = self.event_bus.publish(AgentEvent::TaskStarted {
            task_id,
            agent_name: "TaskManager(rust_bridge_agent)".to_string(),
            input_summary: format!(
                "X profili kazınıyor: {}, ritüeller: {}, playlist: {}, envies: {}",
                target_url,
                user_rituals.join(", "),
                user_playlist.join(", "),
                user_envies.join(", ")
            ),
        });

        // Proje kökünü bul
        let manifest_dir = std::env::var("CARGO_MANIFEST_DIR")
            .unwrap_or_else(|_| "/workspace/rust_core".to_string());
        let project_root = std::path::Path::new(&manifest_dir)
            .parent()
            .map(|p| p.to_string_lossy().to_string())
            .unwrap_or_else(|| "/workspace".to_string());
        let bridge_agent_path = format!("{}/agent_core/agents/rust_bridge_agent.py", project_root);

        // Önce scraper.py ile veriyi çek, sonra rust_bridge_agent.py ile tam pipeline çalıştır
        let python_script = format!(
            r#"
import sys
import json
sys.path.insert(0, '/workspace')

# 1. Adım: Scraper ile profil verisini çek
from scraper import scrape_readonly

try:
    profile_data = scrape_readonly('{}')
    
    if not profile_data or 'error' in profile_data:
        print(json.dumps({{"status": "error", "message": "Scraper başarısız", "data": profile_data}}))
        sys.exit(0)
    
    # 2. Adım: Kullanıcı frekans parametrelerini hazırla
    user_freq = {{
        "rituals": {},
        "playlist": {},
        "envies": {}
    }}
    
    # 3. Adım: rust_bridge_agent.py ile tam analiz pipeline'ını çalıştır
    sys.argv = ['rust_bridge_agent.py', '{}', json.dumps(profile_data), json.dumps(user_freq)]
    
    # Import ve çalıştır
    from agent_core.agents.rust_bridge_agent import run_full_pipeline
    final_report = run_full_pipeline('{}', profile_data, user_freq)
    
    # 4. Adım: Sonucu JSON olarak döndür
    output = {{
        "status": "success",
        "data": final_report
    }}
    print(json.dumps(output))
    
except Exception as e:
    import traceback
    error_detail = traceback.format_exc()
    print(json.dumps({{
        "status": "error",
        "message": str(e),
        "traceback": error_detail
    }}))
"#,
            target_url,
            serde_json::to_string(&user_rituals).unwrap_or("[]".to_string()),
            serde_json::to_string(&user_playlist).unwrap_or("[]".to_string()),
            serde_json::to_string(&user_envies).unwrap_or("[]".to_string()),
            target_url,
            target_url
        );

        let output = Command::new(&self.python_path)
            .arg("-c")
            .arg(python_script)
            .output()
            .await
            .map_err(|e| format!("Python süreci başlatılamadı: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);

        // Hata durumunda EventBus'a bildir
        if !output.status.success() || stderr.contains("Error") || stderr.contains("Exception") {
            let _ = self.event_bus.publish(AgentEvent::ErrorHalt {
                task_id,
                agent_name: "TaskManager(PinealExecutor)".to_string(),
                error_code: "PYTHON_EXECUTOR_FAILED".to_string(),
                error_message: format!("{}\n{}", stderr, stdout),
                severity: Severity::Critical,
            });
            return Err(format!("Executor hatası: {}", stderr));
        }

        // JSON çıktıyı parse et
        let json_result: Value = serde_json::from_str(&stdout)
            .map_err(|e| format!("JSON parse hatası: {}, çıktı: {}", e, stdout))?;

        // Error kontrolü
        if let Some(status) = json_result.get("status") {
            if status.as_str() == Some("error") {
                let error_msg = json_result
                    .get("message")
                    .and_then(|v| v.as_str())
                    .unwrap_or("Bilinmeyen hata");
                let _ = self.event_bus.publish(AgentEvent::ErrorHalt {
                    task_id,
                    agent_name: "TaskManager(PinealExecutor)".to_string(),
                    error_code: "EXECUTOR_ERROR".to_string(),
                    error_message: error_msg.to_string(),
                    severity: Severity::High,
                });
                return Err(format!("Executor hatası: {}", error_msg));
            }
        }

        // Başarılı sonuç - EventBus'a telemetry gönder
        let data = json_result.get("data").unwrap_or(&json_result);
        
        // Frekans verilerini çıkar ve FrequencyUpdate event'i yayınla
        if let Some(analysis) = data.get("mirror_analysis") {
            let ritual_score = analysis.get("ritual_match_score").and_then(|v| v.as_f64()).unwrap_or(0.0) as f32;
            let playlist_score = analysis.get("playlist_resonance").and_then(|v| v.as_f64()).unwrap_or(0.0) as f32;
            let envy_score = analysis.get("envy_intensity").and_then(|v| v.as_f64()).unwrap_or(0.0) as f32;
            let overall_freq = analysis.get("user_core_frequency").and_then(|v| v.as_str()).unwrap_or("unknown").to_string();
            
            let _ = self.event_bus.publish(AgentEvent::FrequencyUpdate {
                task_id,
                ritual_match_score: ritual_score,
                playlist_resonance: playlist_score,
                envy_intensity: envy_score,
                overall_frequency: overall_freq,
            });
        }
        
        let _ = self.event_bus.publish(AgentEvent::StepCompleted {
            task_id,
            agent_name: "TaskManager(rust_bridge_agent)".to_string(),
            step_name: "FullPipelineCompleted".to_string(),
            output_hash: format!("{:x}", md5::compute(data.to_string())),
        });

        let _ = self.event_bus.publish(AgentEvent::TaskCompleted {
            task_id,
            agent_name: "TaskManager(rust_bridge_agent)".to_string(),
            final_result_hash: format!("{:x}", md5::compute(stdout.to_string())),
            duration_ms: 150,
        });

        Ok(stdout.to_string())
    }
}
