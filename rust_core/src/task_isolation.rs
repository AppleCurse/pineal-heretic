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

    /// Python scraper.py'yi alt süreç olarak çalıştır ve JSON çıktıyı yakala
    pub async fn execute_isolated_task(&self, target_url: String) -> Result<String, String> {
        let task_id = self.create_task();
        
        let _ = self.event_bus.publish(AgentEvent::TaskStarted {
            task_id,
            agent_name: "TaskManager(Python)".to_string(),
            input_summary: format!("X profili kazınıyor: {}", target_url),
        });

        // Python scraper'ı çalıştır
        let output = Command::new(&self.python_path)
            .arg("-c")
            .arg(format!(
                r#"
import sys
sys.path.insert(0, '/workspace')
from scraper import scrape_readonly
import json

try:
    result = scrape_readonly('{}')
    print(json.dumps({{"status": "success", "data": result}}))
except Exception as e:
    print(json.dumps({{"status": "error", "message": str(e)}}))
"#,
                target_url
            ))
            .output()
            .await
            .map_err(|e| format!("Python süreci başlatılamadı: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);

        if !output.status.success() && stderr.contains("Error") {
            let _ = self.event_bus.publish(AgentEvent::ErrorHalt {
                task_id,
                agent_name: "TaskManager(Python)".to_string(),
                error_code: "PYTHON_SCRAPER_FAILED".to_string(),
                error_message: stderr.to_string(),
                severity: Severity::Critical,
            });
            return Err(format!("Scraper hatası: {}", stderr));
        }

        // JSON çıktıyı parse et
        let json_result: Value = serde_json::from_str(&stdout)
            .map_err(|e| format!("JSON parse hatası: {}, çıktı: {}", e, stdout))?;

        if let Some(error_msg) = json_result.get("message") {
            let _ = self.event_bus.publish(AgentEvent::ErrorHalt {
                task_id,
                agent_name: "TaskManager(Python)".to_string(),
                error_code: "SCRAPER_ERROR".to_string(),
                error_message: error_msg.as_str().unwrap_or("Bilinmeyen hata").to_string(),
                severity: Severity::High,
            });
            return Err(format!("Scraper hatası: {}", error_msg));
        }

        // Başarılı sonuç - EventBus'a telemetry gönder
        let data = json_result.get("data").unwrap_or(&json_result);
        let _ = self.event_bus.publish(AgentEvent::StepCompleted {
            task_id,
            agent_name: "TaskManager(Python)".to_string(),
            step_name: "ScrapeCompleted".to_string(),
            output_hash: format!("{:x}", md5::compute(data.to_string())),
        });

        let _ = self.event_bus.publish(AgentEvent::TaskCompleted {
            task_id,
            agent_name: "TaskManager(Python)".to_string(),
            final_result_hash: format!("{:x}", md5::compute(stdout.to_string())),
            duration_ms: 150,
        });

        Ok(stdout.to_string())
    }
}
