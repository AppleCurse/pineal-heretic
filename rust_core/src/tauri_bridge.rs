use tauri::{AppHandle, Emitter};
use tokio::sync::Mutex;
use std::sync::Arc;
use serde::Serialize;

use crate::aspasia::AspasiaEngine;
use crate::event_bus::{EventBus, TelemetryEvent};
use crate::task_isolation::TaskManager;
use crate::vault::StealthVault;

/// State wrapper to hold our core engines for Tauri
pub struct CoreState {
    pub task_manager: Arc<TaskManager>,
    pub aspasia: Arc<Mutex<AspasiaEngine>>,
    pub vault: Arc<Mutex<StealthVault>>,
    pub event_bus: EventBus,
}

#[derive(Serialize, Clone)]
pub struct TauriEventPayload {
    pub event_type: String,
    pub data: String,
}

/// 1. Tauri IPC Commands

#[tauri::command]
pub async fn start_analysis(target_url: String, state: tauri::State<'_, CoreState>) -> Result<String, String> {
    // Isolated task runner tetiklenir
    let result = state.task_manager.execute_isolated_task(target_url).await;
    result.map_err(|e| format!("Analiz başlatılamadı: {}", e))
}

#[tauri::command]
pub async fn query_aspasia(state: tauri::State<'_, CoreState>) -> Result<String, String> {
    let aspasia = state.aspasia.lock().await;
    let report = aspasia.report_system_overview().await;
    Ok(report)
}

#[tauri::command]
pub async fn set_vault_credentials(_key: String, _value: String, state: tauri::State<'_, CoreState>) -> Result<String, String> {
    // Şimdilik sadece mock olarak döndürüyoruz. Gerçek StealthVault metotları eklendikçe bağlanacak.
    let _vault = state.vault.lock().await;
    Ok(format!("{} başarıyla kasaya eklendi.", _key))
}

/// 2. Canlı Telemetri Köprüsü (EventBus -> Tauri Emit)
pub fn setup_telemetry_bridge(app_handle: AppHandle, mut rx: tokio::sync::broadcast::Receiver<TelemetryEvent>) {
    tauri::async_runtime::spawn(async move {
        while let Ok(event) = rx.recv().await {
            // Event'i JSON'a çevir
            if let Ok(json_str) = serde_json::to_string(&event) {
                let payload = TauriEventPayload {
                    event_type: "telemetry_update".to_string(),
                    data: json_str,
                };
                
                // Tauri arayüzüne (Svelte) gönder
                let _ = app_handle.emit("pineal-telemetry", payload);
            }
        }
    });
}
