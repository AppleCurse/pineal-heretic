use pineal_heretic_core::{
    ChiefEngine, AspasiaEngine, EventBus, TaskManager, StealthVault,
};
use pineal_heretic_core::tauri_bridge::{CoreState, setup_telemetry_bridge};
use std::sync::Arc;
use tokio::sync::Mutex;
use std::path::Path;

// Tauri komutları
#[tauri::command]
async fn start_analysis(target_url: String, state: tauri::State<'_, CoreState>) -> Result<String, String> {
    let result = state.task_manager.execute_isolated_task(target_url).await;
    result.map_err(|e| format!("Analiz başlatılamadı: {}", e))
}

#[tauri::command]
async fn query_aspasia(state: tauri::State<'_, CoreState>) -> Result<String, String> {
    let mut aspasia = state.aspasia.lock().await;
    let report = aspasia.report_system_overview().await;
    Ok(report)
}

#[tauri::command]
async fn set_vault_credentials(key: String, value: String, state: tauri::State<'_, CoreState>) -> Result<String, String> {
    let vault = state.vault.lock().await;
    vault.store(&key, &value).map_err(|e| e.to_string())?;
    Ok(format!("{} başarıyla kasaya şifrelenerek eklendi.", key))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Core bileşenleri başlat
    let event_bus = Arc::new(EventBus::new(100));
    
    let chief = ChiefEngine::new(100);
    
    let aspasia = AspasiaEngine::new(chief, "dummy_api_key".to_string());
    
    let vault = StealthVault::new(Path::new(".pineal_vault")).expect("Vault oluşturulamadı");
    
    let task_manager = TaskManager::new();
    
    // CoreState oluştur
    let core_state = CoreState {
        task_manager: Arc::new(task_manager),
        aspasia: Arc::new(Mutex::new(aspasia)),
        vault: Arc::new(Mutex::new(vault)),
        event_bus: event_bus.clone(),
    };
    
    // Telemetri alıcısı oluştur
    let telemetry_rx = event_bus.subscribe();
    
    // Tauri uygulamasını başlat
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(core_state)
        .invoke_handler(tauri::generate_handler![
            start_analysis,
            query_aspasia,
            set_vault_credentials,
        ])
        .setup(move |app| {
            // Telemetri köprüsünü kur
            use tauri::Manager;
            let app_handle = app.handle().clone();
            setup_telemetry_bridge(app_handle, telemetry_rx);
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
