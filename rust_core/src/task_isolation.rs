use uuid::Uuid;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use crate::event_bus::EventBus;
use crate::agents::autonomous_verifier::AutonomousVerifier;
use crate::agent_pipeline::AgentNode;

#[derive(Debug, Clone)]
pub struct TaskContext {
    pub task_id: Uuid,
    pub state: HashMap<String, String>,
}

pub struct TaskManager {
    tasks: Arc<Mutex<HashMap<Uuid, TaskContext>>>,
}

impl TaskManager {
    pub fn new() -> Self {
        Self {
            tasks: Arc::new(Mutex::new(HashMap::new())),
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

    pub async fn execute_isolated_task(&self, target_url: String, event_bus: Arc<EventBus>) -> Result<String, String> {
        let task_id = self.create_task();
        let verifier = AutonomousVerifier::new(event_bus);
        
        // Gerçek OSINT taramasını ve telemetry'yi tetikler
        let result = verifier.execute(&target_url).await
            .map_err(|e| format!("Görev {} başarısız oldu: {:?}", task_id, e))?;
            
        Ok(format!("Görev {} tamamlandı. Bulgu: {}", task_id, result.payload))
    }
}
