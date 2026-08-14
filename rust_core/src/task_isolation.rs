//! PINEAL-HERETIC v4.0 - Task Isolation
//! 
//! Her görevi bellek açısından izole eder, çapraz bulaşmayı engeller.

use crate::event_bus::{EventBus, AgentEvent};
use crate::chief::ChiefEngine;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use uuid::Uuid;

/// Görev bağlamı - her task için izolasyon metaverisi
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskContext {
    pub task_id: Uuid,
    pub target_url: String,
    pub started_at: chrono::DateTime<chrono::Utc>,
    pub status: TaskStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaskStatus {
    Pending,
    Running,
    Completed,
    Failed(String),
    Halted(String),
}

/// Task Manager - İzole görev yürütücü
pub struct TaskManager {
    event_bus: EventBus,
    chief: Arc<Mutex<ChiefEngine>>,
    active_tasks: Arc<Mutex<std::collections::HashMap<Uuid, TaskContext>>>,
}

impl TaskManager {
    pub fn new(event_bus: EventBus, chief: ChiefEngine) -> Self {
        Self {
            event_bus,
            chief: Arc::new(Mutex::new(chief)),
            active_tasks: Arc::new(Mutex::new(std::collections::HashMap::new())),
        }
    }

    /// İzole görev başlat
    pub async fn execute_isolated_task(&self, target_url: String) -> Result<String, String> {
        let task_id = Uuid::new_v4();
        
        // Görev bağlamını oluştur
        let context = TaskContext {
            task_id,
            target_url: target_url.clone(),
            started_at: chrono::Utc::now(),
            status: TaskStatus::Pending,
        };

        // Aktif görevlere ekle
        {
            let mut tasks = self.active_tasks.lock().await;
            tasks.insert(task_id, context);
        }

        // Event yayınla - Task Started
        let _ = self.event_bus.publish(AgentEvent::TaskStarted {
            task_id,
            agent_name: "TaskManager".to_string(),
            input_summary: format!("Hedef URL analizi: {}", target_url),
        });

        // Görevi çalıştır (simülasyon - gerçek analiz pipeline'ı buraya gelecek)
        let result = self.run_task_simulation(task_id, &target_url).await;

        // Durumu güncelle
        {
            let mut tasks = self.active_tasks.lock().await;
            if let Some(ctx) = tasks.get_mut(&task_id) {
                ctx.status = match &result {
                    Ok(_) => TaskStatus::Completed,
                    Err(e) => TaskStatus::Failed(e.clone()),
                };
            }
        }

        // Event yayınla - Task Completed/Failed
        match &result {
            Ok(output) => {
                let _ = self.event_bus.publish(AgentEvent::TaskCompleted {
                    task_id,
                    agent_name: "TaskManager".to_string(),
                    final_result_hash: format!("{:x}", md5::compute(output.as_bytes())),
                    duration_ms: 0, // Gerçek süre hesaplanacak
                });
                Ok(format!("Görev {} tamamlandı: {}", task_id, output))
            }
            Err(e) => {
                let _ = self.event_bus.publish(AgentEvent::ErrorHalt {
                    task_id,
                    agent_name: "TaskManager".to_string(),
                    error_code: "TASK_EXECUTION_FAILED".to_string(),
                    error_message: e.clone(),
                    severity: crate::event_bus::Severity::Critical,
                });
                Err(format!("Görev {} başarısız: {}", task_id, e))
            }
        }
    }

    /// Görev simülasyonu (gerçek analiz pipeline'ı buraya entegre edilecek)
    async fn run_task_simulation(&self, task_id: Uuid, target_url: &str) -> Result<String, String> {
        // Simüle edilmiş analiz adımları
        tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;

        // Adım 1: URL doğrulama
        let _ = self.event_bus.publish(AgentEvent::StepCompleted {
            task_id,
            agent_name: "TaskManager".to_string(),
            step_name: "URL_Validation".to_string(),
            output_hash: format!("{:x}", md5::compute(target_url.as_bytes())),
        });

        tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;

        // Adım 2: Analiz tamamlama
        let result = format!("Analiz tamamlandı: {}", target_url);
        
        Ok(result)
    }

    /// Görev durumunu al
    pub async fn get_task_status(&self, task_id: &Uuid) -> Option<TaskContext> {
        let tasks = self.active_tasks.lock().await;
        tasks.get(task_id).cloned()
    }

    /// Tüm aktif görevleri listele
    pub async fn list_active_tasks(&self) -> Vec<TaskContext> {
        let tasks = self.active_tasks.lock().await;
        tasks.values().cloned().collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::event_bus::EventBus;
    use crate::chief::ChiefEngine;

    #[tokio::test]
    async fn test_task_manager_isolation() {
        let event_bus = EventBus::new(100);
        let chief = ChiefEngine::new(100);
        let manager = TaskManager::new(event_bus, chief);

        // İki bağımsız görev başlat
        let result1 = manager.execute_isolated_task("https://example1.com".to_string()).await;
        let result2 = manager.execute_isolated_task("https://example2.com".to_string()).await;

        assert!(result1.is_ok());
        assert!(result2.is_ok());
        assert_ne!(result1.unwrap(), result2.unwrap());
    }
}
