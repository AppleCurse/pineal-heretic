use tokio::process::{Child, Command};
use std::process::Stdio;

/// Represents an isolated browser process (e.g., CloakBrowser or Playwright worker)
/// Uses Rust's Drop trait to absolutely ensure no zombie processes remain.
pub struct GhostBrowser {
    process: Option<Child>,
    session_id: String,
}

impl GhostBrowser {
    pub async fn spawn(executable_path: &str, target_url: &str) -> Result<Self, String> {
        let child = Command::new(executable_path)
            .arg("--headless")
            .arg("--disable-gpu")
            .arg(target_url)
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .kill_on_drop(true) // Crucial Tokio feature: kills the process if dropped
            .spawn()
            .map_err(|e| format!("Failed to spawn GhostBrowser: {}", e))?;

        let session_id = uuid::Uuid::new_v4().to_string();
        println!("[GHOST] Spawned browser session: {}", session_id);

        Ok(Self {
            process: Some(child),
            session_id,
        })
    }

    pub fn session_id(&self) -> &str {
        &self.session_id
    }
    
    pub async fn terminate(&mut self) {
        if let Some(mut child) = self.process.take() {
            println!("[GHOST] Terminating browser session: {}", self.session_id);
            let _ = child.kill().await;
        }
    }
}

impl Drop for GhostBrowser {
    fn drop(&mut self) {
        // Even if the program panics, Drop is called.
        // If `terminate` wasn't explicitly called, the process is still running.
        // `kill_on_drop(true)` ensures the OS kills the process.
        if self.process.is_some() {
            println!("[GHOST-DROP] Panic or scope exit detected. Zombie process destroyed for session: {}", self.session_id);
        }
    }
}
