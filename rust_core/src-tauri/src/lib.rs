use pineal_heretic_core::{
    ChiefEngine, AspasiaEngine, EventBus, TaskManager,
};
use pineal_heretic_core::tauri_bridge::*;
use pineal_heretic_core::aspasia_bridge::*;
use std::sync::Arc;
use tokio::sync::Mutex;



#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Core bileşenleri başlat
    let event_bus = Arc::new(EventBus::new(100));
    
    let chief = ChiefEngine::new(100);
    
    let aspasia = AspasiaEngine::new(chief, "dummy_api_key".to_string());
    
    let task_manager = TaskManager::new();
    
    // CoreState oluştur (Vault başlangıçta kilitli)
    let core_state = CoreState {
        task_manager: Arc::new(task_manager),
        aspasia: Arc::new(Mutex::new(aspasia)),
        vault: Arc::new(Mutex::new(None)),
        event_bus: event_bus.clone(),
        aspasia_bridge: AspasiaBridge,
    };
    
    // Telemetri alıcısı oluştur
    let telemetry_rx = event_bus.subscribe();
    
    // Tauri uygulamasını başlat
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(core_state)
        .invoke_handler(tauri::generate_handler![
            unlock_vault,
            start_analysis,
            query_aspasia,
            set_vault_credentials,
            analyze_with_aspasia,
            analyze_target_real,
            consult_aspasia,
            run_osint_scraper,
        ])
        .setup(move |app| {
            // Telemetri köprüsünü kur
            
            let app_handle = app.handle().clone();
            setup_telemetry_bridge(app_handle, telemetry_rx);
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
