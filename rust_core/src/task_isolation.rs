use std::sync::Arc;
use tokio::sync::Mutex;
use uuid::Uuid;
use crate::agent_pipeline::{AgentNode, HaltReason};
use crate::MirrorTruthAgent;
use crate::ghost::GhostBrowser;

pub struct TaskContext {
    pub task_id: String,
    pub payload: String,
}

pub struct TaskManager {
    active_tasks: Arc<Mutex<Vec<String>>>,
}

impl TaskManager {
    pub fn new() -> Self {
        Self {
            active_tasks: Arc::new(Mutex::new(Vec::new())),
        }
    }

    /// Spawns an isolated Tokio task. Each task handles its own GhostBrowser and Agent Pipeline.
    /// Memory is strictly isolated to prevent deadlocks.
    pub async fn execute_isolated_task(&self, target_url: String) -> Result<String, String> {
        let task_id = Uuid::new_v4().to_string();
        
        {
            let mut tasks = self.active_tasks.lock().await;
            tasks.push(task_id.clone());
        }

        let task_id_clone = task_id.clone();
        
        // Spawn isolated thread
        let handle = tokio::spawn(async move {
            println!("[TASK:{}] Initiated.", task_id_clone);
            
            // 1. Initialize GhostBrowser (CloakBrowser integration)
            let executable_path = if cfg!(windows) {
                "C:\\Windows\\System32\\cmd.exe" // Placeholder dummy executable for testing
            } else {
                "/bin/echo" // Placeholder
            };
            
            let mut ghost = GhostBrowser::spawn(executable_path, &target_url)
                .await
                .map_err(|e| format!("GhostBrowser spawn failed: {}", e))?;
                
            // Simulate scrape (in reality, wait for Crawl4AI output)
            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
            let scraped_data = "dummy_scraped_data_from_cloak";
            
            // 2. Pass to Strict Pipeline
            let bus = crate::event_bus::EventBus::new(10);
            let mirror = MirrorTruthAgent::new(bus);
            match mirror.execute(scraped_data).await {
                Ok(res) => {
                    println!("[TASK:{}] Pipeline Success. Confidence: {}", task_id_clone, res.confidence);
                },
                Err(HaltReason::InsufficientEvidence(reason)) => {
                    println!("[TASK:{}] Pipeline HALTED: {}", task_id_clone, reason);
                    return Err(format!("HALTED: {}", reason));
                },
                Err(_) => {
                    println!("[TASK:{}] Pipeline Error.", task_id_clone);
                    return Err("Pipeline Error".into());
                }
            }
            
            ghost.terminate().await;
            Ok(format!("Task {} completed successfully.", task_id_clone))
        });

        // Await the task result
        match handle.await {
            Ok(Ok(res)) => Ok(res),
            Ok(Err(e)) => Err(e),
            Err(e) => Err(format!("Task panic isolated and caught: {}", e)),
        }
    }
}
