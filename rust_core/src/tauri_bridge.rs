use tauri::{AppHandle, Emitter};
use tokio::sync::Mutex;
use std::sync::Arc;
use serde::{Deserialize, Serialize};
use std::path::Path;

use crate::chief::ChiefEngine;
use crate::aspasia::AspasiaEngine;
use crate::event_bus::{EventBus, TelemetryEvent};
use crate::task_isolation::TaskManager;
use crate::vault::StealthVault;

/// State wrapper to hold our core engines for Tauri
pub struct CoreState {
    pub task_manager: Arc<TaskManager>,
    pub aspasia: Arc<Mutex<AspasiaEngine>>,
    pub vault: Arc<Mutex<Option<StealthVault>>>,
    pub event_bus: Arc<EventBus>,
    pub aspasia_bridge: crate::aspasia_bridge::AspasiaBridge,
}

#[derive(Serialize, Clone)]
pub struct TauriEventPayload {
    pub event_type: String,
    pub data: String,
}

/// 1. Tauri IPC Commands

#[tauri::command]
pub async fn unlock_vault(password: String, state: tauri::State<'_, CoreState>) -> Result<String, String> {
    let vault_path = Path::new(".pineal_vault");
    
    let vault = if vault_path.exists() {
        StealthVault::load(vault_path, &password).map_err(|e| e.to_string())?
    } else {
        StealthVault::new(vault_path, &password).map_err(|e| e.to_string())?
    };
    
    let mut state_vault = state.vault.lock().await;
    *state_vault = Some(vault);
    
    Ok("Vault unlocked successfully".to_string())
}

#[tauri::command]
pub async fn start_analysis(target_url: String, state: tauri::State<'_, CoreState>) -> Result<String, String> {
    let result = state.task_manager.execute_isolated_task(target_url, state.event_bus.clone()).await;
    result.map_err(|e| format!("Analiz başlatılamadı: {}", e))
}

#[tauri::command]
pub async fn query_aspasia(user_message: String, state: tauri::State<'_, CoreState>) -> Result<String, String> {
    // Kullanıcıdan gelen mesajı AspasiaEngine veya AspasiaBridge'e gönder
    // Mevcut mimaride aspasia_bridge Python motoruna bağlanır
    
    // Hedef datasını sahte bir yapıyla iletiyoruz (bunu UI'dan da alabilirsiniz)
    let payload = serde_json::json!({
        "social_media_texts": [user_message],
        "message_frequency": 2.5
    });

    let result = state.aspasia_bridge.analyze_target(payload)
        .map_err(|e| e.to_string())?;
        
    let json_response = serde_json::to_string_pretty(&result)
        .unwrap_or_else(|_| "Serialization error".to_string());
        
    Ok(json_response)
}

#[tauri::command]
pub async fn set_vault_credentials(key: String, value: String, state: tauri::State<'_, CoreState>) -> Result<String, String> {
    let vault_guard = state.vault.lock().await;
    if let Some(vault) = vault_guard.as_ref() {
        vault.store(&key, &value).map_err(|e| e.to_string())?;
        Ok(format!("'{}' anahtarı başarıyla kasaya şifrelendi.", key))
    } else {
        Err("Vault kilitli veya parola girilmedi.".to_string())
    }
}

/// 2. Canlı Telemetri Köprüsü (EventBus -> Tauri Emit)
pub fn setup_telemetry_bridge(app_handle: AppHandle, mut rx: tokio::sync::broadcast::Receiver<TelemetryEvent>) {
    tauri::async_runtime::spawn(async move {
        while let Ok(event) = rx.recv().await {
            if let Ok(json_str) = serde_json::to_string(&event) {
                let payload = TauriEventPayload {
                    event_type: "telemetry_update".to_string(),
                    data: json_str,
                };
                let _ = app_handle.emit("pineal-telemetry", payload);
            }
        }
    });
}
